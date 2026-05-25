"""DataUpdateCoordinator for Grünbeck Cloud SE Series."""
from __future__ import annotations

from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from pygruenbeck_cloud import PyGruenbeckCloud

from .const import DEFAULT_SCAN_INTERVAL, DOMAIN, LOGGER


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

        super().__init__(
            hass,
            LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=scan_interval),
        )


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
            BASE_URL = "https://prod-eu-gruenbeck-api.azurewebsites.net/api/devices"
            API_VERSION = "2024-05-02"
            url_base = f"{BASE_URL}/{self.device_id}"

            headers = {
                "Authorization": f"Bearer {token}",
                "User-Agent": "pygruenbeck_cloud",
                "Accept": "application/json",
            }

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

            return update_data

        except Exception as err:
            raise UpdateFailed(
                f"Error communicating with Grünbeck Cloud API: {err}"
            ) from err
