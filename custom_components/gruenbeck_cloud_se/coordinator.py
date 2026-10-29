"""DataUpdateCoordinator for Grünbeck Cloud SE Series."""
from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

from homeassistant.core import CALLBACK_TYPE, HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.event import async_call_later
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util
from pygruenbeck_cloud import PyGruenbeckCloud

from .const import (
    API_BASE_URL,
    API_VERSION,
    DOMAIN,
    EXTRA_SCAN_INTERVAL,
    LIVE_MODE_DURATION,
    LIVE_MODE_INTERVAL,
    LOGGER,
    REGENERATION_TRACKING_INTERVAL,
    REGENERATION_TRACKING_MAX,
)
from .models import DeviceFeatures, device_features

# Fields of the /update payload that are not device measurements
IGNORED_CHANGE_KEYS = {"id", "name", "serialNumber", "series", "type", "register", "isRegistered"}

# Plain cloud endpoints (no realtime commands to the device).
# Key in coordinator data -> endpoint suffix
EXTRA_ENDPOINTS = {
    "_info": "",
    "_parameters": "/parameters",
    "_water": "/measurements/water",
    "_salt": "/measurements/salt",
}

# Sources watched for changed settings: device info and parameters.
# Fields that change on their own are ignored.
WATCHED_CHANGE_SOURCES = ("_info", "_parameters")
IGNORED_SETTING_KEYS = {"pdate", "regMo1", "$pending"}
MAX_SETTING_CHANGES = 50


class GruenbeckDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching Grünbeck Cloud data."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: PyGruenbeckCloud,
        device_id: str,
        scan_interval: int,
    ) -> None:
        """Initialize the coordinator."""
        self.api = api
        self.device_id = device_id

        # Cached results of the plain cloud endpoints
        self.extra_data: dict[str, Any] = {}
        self._extra_last_fetch: datetime | None = None

        # Detection of frozen cloud data
        self._last_update_data: dict[str, Any] | None = None
        self.last_data_change: datetime | None = None
        self.last_poll: datetime | None = None

        # Live mode
        self._default_interval = timedelta(minutes=scan_interval)
        self._live_mode_unsub: CALLBACK_TYPE | None = None

        # Dates of the last maintenance and inspection. The cloud does not
        # know them, so they are stored locally.
        self.service_dates: dict[str, date | None] = {
            "maintenance": None,
            "inspection": None,
        }
        self._service_store: Store = Store(
            hass, 1, f"{DOMAIN}_{device_id}_service_dates"
        )

        # Log of changed settings, e.g. to find out which parameter an app
        # option corresponds to
        self.setting_changes: list[dict[str, Any]] = []
        self._changes_store: Store = Store(
            hass, 1, f"{DOMAIN}_{device_id}_setting_changes"
        )

        # Faster polling while a regeneration is running (switch, default off)
        self.track_regeneration = False
        self._regeneration_started: datetime | None = None

        super().__init__(
            hass,
            LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=scan_interval),
        )

    def _headers(self, token: str) -> dict[str, str]:
        """Return request headers."""
        return {
            "Authorization": f"Bearer {token}",
            "User-Agent": "pygruenbeck_cloud",
            "Accept": "application/json",
        }

    async def _async_fetch_extra_data(self, token: str) -> None:
        """Fetch device info, parameters and daily measurements.

        These endpoints only read the cloud cache and do not wake up the
        device, so they are safe with respect to rate limiting. Failures are
        logged and the previous values are kept.
        """
        now = dt_util.utcnow()
        if self._extra_last_fetch is not None and now - self._extra_last_fetch < timedelta(
            minutes=EXTRA_SCAN_INTERVAL
        ):
            return

        url_base = f"{API_BASE_URL}/{self.device_id}"
        for data_key, endpoint in EXTRA_ENDPOINTS.items():
            url = f"{url_base}{endpoint}?api-version={API_VERSION}"
            try:
                async with self.api.session.get(
                    url, headers=self._headers(token)
                ) as resp:
                    if resp.status != 200:
                        LOGGER.debug(
                            "HTTP error %d during GET %s: %s",
                            resp.status,
                            endpoint or "/",
                            await resp.text(),
                        )
                        continue
                    new = await resp.json()
                    if data_key in WATCHED_CHANGE_SOURCES:
                        self._record_setting_changes(
                            data_key, self.extra_data.get(data_key), new
                        )
                    self.extra_data[data_key] = new
            except Exception as err:  # noqa: BLE001
                LOGGER.debug("Exception during GET %s: %s", endpoint or "/", err)

        self._extra_last_fetch = now
        if self._changes_dirty:
            self._changes_dirty = False
            self._changes_store.async_delay_save(
                lambda: {"changes": self.setting_changes}, 5
            )

    _changes_dirty = False

    def _record_setting_changes(
        self, source: str, old: Any, new: Any
    ) -> None:
        """Remember which settings changed since the last fetch."""
        if not isinstance(old, dict) or not isinstance(new, dict):
            return
        time = dt_util.now().isoformat(timespec="seconds")
        for key in sorted(set(old) | set(new)):
            if key in IGNORED_SETTING_KEYS or old.get(key) == new.get(key):
                continue
            self.setting_changes.insert(
                0,
                {
                    "time": time,
                    "source": source.lstrip("_"),
                    "key": key,
                    "old": old.get(key),
                    "new": new.get(key),
                },
            )
            LOGGER.info("Setting %s changed: %s -> %s", key, old.get(key), new.get(key))
            self._changes_dirty = True
        del self.setting_changes[MAX_SETTING_CHANGES:]

    async def async_load_setting_changes(self) -> None:
        """Load the stored log of changed settings."""
        stored = await self._changes_store.async_load() or {}
        changes = stored.get("changes")
        if isinstance(changes, list):
            self.setting_changes = changes[:MAX_SETTING_CHANGES]

    async def async_refresh_settings(self) -> None:
        """Fetch device info and parameters now, without waking the device."""
        try:
            token = await self.api._get_web_access_token()
            if self.api.session is None or self.api.session.closed:
                await self.api.login()
                token = await self.api._get_web_access_token()
        except Exception as err:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="command_failed",
                translation_placeholders={"error": str(err)},
            ) from err
        self._extra_last_fetch = None
        await self._async_fetch_extra_data(token)
        if self.data is not None:
            self.async_set_updated_data({**self.data, **self.extra_data})

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from Grünbeck Cloud using the 5-step realtime sequence."""
        try:
            # Get valid token (this automatically logs in or refreshes if expired)
            token = await self.api._get_web_access_token()

            # Make sure we have a session to perform our custom sequence
            if self.api.session is None or self.api.session.closed:
                # If the library closed the session, we re-login to re-create it
                await self.api.login()
                token = await self.api._get_web_access_token()

            # Execute the 5-step sequence
            url_base = f"{API_BASE_URL}/{self.device_id}"
            headers = self._headers(token)

            steps = [
                ("POST", "/realtime/refresh"),
                ("POST", "/realtime/enter"),
                ("GET", "/update"),
                ("POST", "/realtime/leave"),
                ("POST", "/realtime/off"),
            ]

            update_data = None
            for method, endpoint in steps:
                url = f"{url_base}{endpoint}?api-version={API_VERSION}"
                try:
                    if method == "GET":
                        async with self.api.session.get(
                            url, headers=headers
                        ) as resp:
                            if resp.status != 200:
                                LOGGER.warning(
                                    "HTTP error %d during GET %s: %s",
                                    resp.status,
                                    endpoint,
                                    await resp.text(),
                                )
                            elif endpoint == "/update":
                                update_data = await resp.json()
                    else:
                        async with self.api.session.post(
                            url, headers=headers, json={}
                        ) as resp:
                            if resp.status not in (200, 204):
                                LOGGER.warning(
                                    "HTTP error %d during POST %s: %s",
                                    resp.status,
                                    endpoint,
                                    await resp.text(),
                                )
                except Exception as step_err:
                    LOGGER.warning(
                        "Exception during endpoint %s: %s", endpoint, step_err
                    )

            if not update_data:
                raise UpdateFailed("Failed to retrieve real-time update data")


            # Verify the response represents a valid update dictionary
            if not isinstance(update_data, dict):
                raise UpdateFailed(
                    f"Invalid API response format: {type(update_data)}"
                )

            await self._async_fetch_extra_data(token)

            measurements = {
                k: v for k, v in update_data.items() if k not in IGNORED_CHANGE_KEYS
            }
            if measurements != self._last_update_data:
                self._last_update_data = measurements
                self.last_data_change = dt_util.utcnow()

            self._update_regeneration_tracking(update_data)
            self.last_poll = dt_util.utcnow()

            return {**update_data, **self.extra_data}

        except Exception as err:
            raise UpdateFailed(
                f"Error communicating with Grünbeck Cloud API: {err}"
            ) from err

    @property
    def features(self) -> DeviceFeatures:
        """Return the model specific features of the device."""
        return device_features(self.data)

    @property
    def regeneration_tracking_active(self) -> bool:
        """Return True while a regeneration is followed with faster polling."""
        if not self.track_regeneration or self._regeneration_started is None:
            return False
        return dt_util.utcnow() - self._regeneration_started < timedelta(
            minutes=REGENERATION_TRACKING_MAX
        )

    def _update_regeneration_tracking(self, update_data: dict[str, Any]) -> None:
        """Remember when a regeneration started and adjust the interval."""
        try:
            regenerating = int(update_data.get("mregstatus") or 0) != 0
        except (TypeError, ValueError):
            regenerating = False
        if not regenerating:
            self._regeneration_started = None
        elif self._regeneration_started is None:
            self._regeneration_started = dt_util.utcnow()
            if self.track_regeneration:
                LOGGER.info("Regeneration detected, polling every %s seconds",
                            REGENERATION_TRACKING_INTERVAL)
        self._apply_interval()

    def _apply_interval(self) -> None:
        """Set the polling interval for the current mode."""
        if self.live_mode:
            self.update_interval = timedelta(seconds=LIVE_MODE_INTERVAL)
        elif self.regeneration_tracking_active:
            self.update_interval = timedelta(seconds=REGENERATION_TRACKING_INTERVAL)
        else:
            self.update_interval = self._default_interval

    @property
    def live_mode(self) -> bool:
        """Return True while live mode is active."""
        return self._live_mode_unsub is not None

    async def async_start_live_mode(self) -> None:
        """Poll every LIVE_MODE_INTERVAL seconds for LIVE_MODE_DURATION seconds."""
        if self._live_mode_unsub is not None:
            self._live_mode_unsub()
        self._live_mode_unsub = async_call_later(
            self.hass, LIVE_MODE_DURATION, self._async_live_mode_timeout
        )
        self._apply_interval()
        LOGGER.info("Live mode started for %s seconds", LIVE_MODE_DURATION)
        await self.async_refresh()

    async def async_stop_live_mode(self) -> None:
        """Return to the normal polling interval."""
        if self._live_mode_unsub is not None:
            self._live_mode_unsub()
            self._live_mode_unsub = None
        self._apply_interval()
        LOGGER.info("Live mode stopped")
        # Reschedule with the normal interval
        await self.async_refresh()

    async def async_shutdown_live_mode(self) -> None:
        """Cancel the live mode timer on unload."""
        if self._live_mode_unsub is not None:
            self._live_mode_unsub()
            self._live_mode_unsub = None

    async def _async_live_mode_timeout(self, _now: datetime) -> None:
        """Stop live mode after the timeout."""
        self._live_mode_unsub = None
        await self.async_stop_live_mode()

    async def _async_send(self, method: str, endpoint: str, payload: dict[str, Any]) -> Any:
        """Send a command to the cloud and return the JSON response."""
        try:
            token = await self.api._get_web_access_token()
            if self.api.session is None or self.api.session.closed:
                await self.api.login()
                token = await self.api._get_web_access_token()
            url = f"{API_BASE_URL}/{self.device_id}{endpoint}?api-version={API_VERSION}"
            headers = {**self._headers(token), "Content-Type": "application/json"}
            async with self.api.session.request(
                method, url, headers=headers, json=payload
            ) as resp:
                try:
                    response = await resp.json(content_type=None)
                except ValueError:
                    response = await resp.text()
                if resp.status not in (200, 202, 204):
                    raise HomeAssistantError(
                        translation_domain=DOMAIN,
                        translation_key="command_failed",
                        translation_placeholders={"error": f"HTTP {resp.status}: {response}"},
                    )
                return response
        except HomeAssistantError:
            raise
        except Exception as err:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="command_failed",
                translation_placeholders={"error": str(err)},
            ) from err

    async def async_set_parameter(self, key: str, value: Any) -> None:
        """Change a single device parameter."""
        response = await self._async_send("PATCH", "/parameters", {key: value})
        if isinstance(response, dict) and "error" in response:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="command_failed",
                translation_placeholders={"error": str(response["error"])},
            )
        params = dict(self.extra_data.get("_parameters") or {})
        if isinstance(response, dict) and key in response:
            params = response
        else:
            params[key] = value
        self.extra_data["_parameters"] = params
        if self.data is not None:
            self.async_set_updated_data({**self.data, "_parameters": params})
        LOGGER.info("Parameter %s set to %s", key, value)

    async def async_load_service_dates(self) -> None:
        """Load the locally stored maintenance and inspection dates."""
        stored = await self._service_store.async_load() or {}
        for kind in self.service_dates:
            try:
                self.service_dates[kind] = date.fromisoformat(stored[kind])
            except (KeyError, TypeError, ValueError):
                self.service_dates[kind] = None

    async def async_set_service_date(self, kind: str, value: date) -> None:
        """Store the date of the last maintenance or inspection."""
        self.service_dates[kind] = value
        await self._service_store.async_save(
            {k: v.isoformat() if v else None for k, v in self.service_dates.items()}
        )
        self.async_update_listeners()

    def last_service_date(self, kind: str) -> date | None:
        """Return the last service date, the start-up date as fallback."""
        if self.service_dates.get(kind) is not None:
            return self.service_dates[kind]
        startup = ((self.data or {}).get("_info") or {}).get("startUp")
        try:
            return datetime.strptime(str(startup)[:10], "%Y.%m.%d").date()
        except ValueError:
            return None

    def next_service_date(self, kind: str) -> date | None:
        """Return last service date plus the configured interval."""
        key = "pmaintint" if kind == "maintenance" else "pinspect"
        interval = ((self.data or {}).get("_parameters") or {}).get(key)
        last = self.last_service_date(kind)
        if last is None or not isinstance(interval, (int, float)) or interval <= 0:
            return None
        return last + timedelta(days=int(interval))
