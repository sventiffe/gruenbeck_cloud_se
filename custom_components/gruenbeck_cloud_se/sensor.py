"""Support for Grünbeck Cloud SE sensors."""
from __future__ import annotations

from collections.abc import Callable
from datetime import date, datetime, timedelta
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import DOMAIN, REGENERATION_STEPS
from .coordinator import GruenbeckDataUpdateCoordinator
from .entity import GruenbeckEntity

SENSOR_TYPES = {
    "mrescapa1": {
        "name": "Exchanger 1 Remaining Capacity",
        "unit": "L",
        "device_class": SensorDeviceClass.VOLUME,
        "state_class": None,
    },
    "mresidcap1": {
        "name": "Exchanger 1 Remaining Capacity Percent",
        "unit": "%",
        "device_class": None,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "mcapacity": {
        "name": "Regeneration Capacity",
        "unit": "m³",
        "device_class": SensorDeviceClass.VOLUME,
        "state_class": None,
    },
    "mcountreg": {
        "name": "Regeneration Count",
        "unit": None,
        "device_class": None,
        "state_class": SensorStateClass.TOTAL_INCREASING,
    },
    "msaltusage": {
        "name": "Salt Usage",
        "unit": "kg",
        "device_class": SensorDeviceClass.WEIGHT,
        "state_class": SensorStateClass.TOTAL_INCREASING,
    },
    "mflow1": {
        "name": "Exchanger 1 Flow Rate",
        "unit": "L/min",
        "device_class": SensorDeviceClass.VOLUME_FLOW_RATE,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "mregstatus": {
        "name": "Regeneration Status",
        "unit": None,
        "device_class": None,
        # A status code, not a measurement: no statistics, no averaged graph
        "state_class": None,
        "enabled_default": False,
    },
}

# Exchanger 2, only on devices with two exchangers (not the softliQ SE)
SECOND_EXCHANGER_SENSOR_TYPES = {
    "mRescapa2": {
        "name": "Exchanger 2 Remaining Capacity",
        "unit": "L",
        "device_class": SensorDeviceClass.VOLUME,
        "state_class": None,
    },
    "mresidcap2": {
        "name": "Exchanger 2 Remaining Capacity Percent",
        "unit": "%",
        "device_class": None,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "mflow2": {
        "name": "Exchanger 2 Flow Rate",
        "unit": "L/min",
        "device_class": SensorDeviceClass.VOLUME_FLOW_RATE,
        "state_class": SensorStateClass.MEASUREMENT,
        "enabled_default": False,
    },
    "mflowblend": {
        "name": "Blended Flow Rate",
        "unit": "L/min",
        "device_class": SensorDeviceClass.VOLUME_FLOW_RATE,
        "state_class": SensorStateClass.MEASUREMENT,
        "enabled_default": False,
    },
}

# Additional fields of the /update payload. Created only if the device
# reports the field.
UPDATE_EXTRA_SENSOR_TYPES = {
    # Not reported by the softliQ SE21
    "mcurrent": {
        "name": "Chlorine Cell Current",
        "unit": "mA",
        "device_class": SensorDeviceClass.CURRENT,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "mcountwater1": {
        "name": "Soft Water Meter Exchanger 1",
        "unit": "m³",
        "device_class": SensorDeviceClass.WATER,
        "state_class": SensorStateClass.TOTAL_INCREASING,
    },
    "mcountwater2": {
        "name": "Soft Water Meter Exchanger 2",
        "unit": "m³",
        "device_class": SensorDeviceClass.WATER,
        "state_class": SensorStateClass.TOTAL_INCREASING,
    },
    # Shown as "Nachspeisemenge" in liters in the app
    "mcountwatertank": {
        "name": "Make-up Water",
        "unit": "L",
        "device_class": SensorDeviceClass.WATER,
        "state_class": SensorStateClass.TOTAL_INCREASING,
    },
    "mmaint": {
        "name": "Next Service In",
        "unit": "d",
        "device_class": SensorDeviceClass.DURATION,
        "state_class": None,
    },
    "mhardsoftw": {
        "name": "Soft Water Hardness Actual",
        "unit": "°dH",
        "device_class": None,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "mlifeadsorb": {
        "name": "Adsorber Exhausted",
        "unit": "%",
        "device_class": None,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "mflowmax": {
        "name": "Peak Flow Rate",
        "unit": "L/min",
        "device_class": SensorDeviceClass.VOLUME_FLOW_RATE,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "mendreg1": {
        "name": "Last Regeneration Exchanger 1",
        "unit": None,
        "device_class": None,
        "state_class": None,
    },
    "mendreg2": {
        "name": "Last Regeneration Exchanger 2",
        "unit": None,
        "device_class": None,
        "state_class": None,
    },
    "mregpercent1": {
        "name": "Regeneration Progress Exchanger 1",
        "unit": "%",
        "device_class": None,
        "state_class": SensorStateClass.MEASUREMENT,
        "enabled_default": False,
    },
    "mremregstep": {
        "name": "Regeneration Step Remaining",
        "unit": None,
        "device_class": None,
        "state_class": SensorStateClass.MEASUREMENT,
        "enabled_default": False,
    },
}


def _first(data: dict[str, Any] | None, *keys: str) -> Any:
    """Return the first non-empty value of the given keys."""
    if not isinstance(data, dict):
        return None
    for key in keys:
        value = data.get(key)
        if value not in (None, "", "--:--"):
            return value
    return None


def _parse_local_datetime(value: Any) -> datetime | None:
    """Parse a naive cloud datetime as local device time."""
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt_util.get_default_time_zone())
    return parsed


def _parse_date(value: Any) -> date | None:
    """Parse a cloud date (yyyy.mm.dd or yyyy-mm-dd)."""
    if not isinstance(value, str):
        return None
    for fmt in ("%Y.%m.%d", "%Y-%m-%d"):
        try:
            return datetime.strptime(value[:10], fmt).date()
        except ValueError:
            continue
    return None


def _latest_error(info: dict[str, Any] | None) -> str | None:
    """Return the message of the newest unresolved error."""
    errors = (info or {}).get("errors")
    if not isinstance(errors, list):
        return None
    open_errors = [e for e in errors if isinstance(e, dict) and not e.get("isResolved")]
    if not open_errors:
        return "OK"
    newest = max(open_errors, key=lambda e: e.get("date") or "")
    return newest.get("message") or newest.get("description") or str(newest.get("errorCode"))


def _yesterday_value(entries: Any, field: str = "value") -> float | None:
    """Return the measurement of yesterday.

    The cloud only provides completed days, so there is no value for today.
    """
    if not isinstance(entries, list):
        return None
    wanted = (dt_util.now().date() - timedelta(days=1)).isoformat()
    for entry in entries:
        if isinstance(entry, dict) and str(entry.get("date", ""))[:10] == wanted:
            return entry.get(field)
    return None


def _recent_entries(entries: Any, field: str = "value") -> dict[str, Any]:
    """Return the last 14 daily values as attributes."""
    if not isinstance(entries, list):
        return {}
    valid = [e for e in entries if isinstance(e, dict) and "date" in e]
    valid.sort(key=lambda e: str(e["date"]))
    return {str(e["date"])[:10]: e.get(field) for e in valid[-14:]}


def _sum_values(entries: Any, factor: float = 1.0) -> float | None:
    """Return the sum of all daily values returned by the cloud."""
    if not isinstance(entries, list):
        return None
    total = sum(
        e.get("value") or 0 for e in entries if isinstance(e, dict)
    )
    return round(total * factor, 3)


def _regeneration_phase(value: Any) -> str | None:
    """Return the regeneration phase as translatable state."""
    if value is None:
        return None
    try:
        return REGENERATION_STEPS.get(int(value), "other")
    except (TypeError, ValueError):
        return "other"


def _regeneration_times(params: dict[str, Any] | None) -> str | None:
    """Return the configured regeneration times (Monday slots)."""
    times = [
        value
        for key in ("pregmo1", "pregmo2", "pregmo3")
        if (value := _first(params, key)) is not None
    ]
    return ", ".join(times) if times else None


def _next_regeneration_window(params: dict[str, Any] | None) -> datetime | None:
    """Return the next configured regeneration time after now.

    In IQ mode the device decides itself whether it regenerates at such a
    time, so this is the next possible slot, not a fixed appointment.
    """
    slots = []
    for key in ("pregmo1", "pregmo2", "pregmo3"):
        value = _first(params, key)
        try:
            hour, minute = (int(part) for part in str(value).split(":"))
        except (TypeError, ValueError):
            continue
        slots.append((hour, minute))
    if not slots:
        return None
    now = dt_util.now()
    candidates = [
        (now + timedelta(days=day)).replace(
            hour=hour, minute=minute, second=0, microsecond=0
        )
        for day in (0, 1)
        for hour, minute in slots
    ]
    return min(c for c in candidates if c > now)


# Sensors based on the plain cloud endpoints (device info, parameters,
# daily measurements). Created only if the endpoint returned data.
CLOUD_SENSOR_TYPES: dict[str, dict[str, Any]] = {
    "regeneration_phase": {
        "name": "Regeneration Phase",
        "source": "mregstatus",
        "device_class": SensorDeviceClass.ENUM,
        "options": list(dict.fromkeys([*REGENERATION_STEPS.values(), "other"])),
        "value_fn": lambda d: _regeneration_phase(d.get("mregstatus")),
        "attributes_fn": lambda d: {"raw_value": d.get("mregstatus")},
    },
    "next_regeneration_window": {
        "name": "Next Regeneration Window",
        "source": "_parameters",
        "device_class": SensorDeviceClass.TIMESTAMP,
        "value_fn": lambda d: _next_regeneration_window(d.get("_parameters")),
    },
    "startup": {
        "name": "Start-up Date",
        "source": "_info",
        "device_class": SensorDeviceClass.DATE,
        "entity_category": EntityCategory.DIAGNOSTIC,
        "value_fn": lambda d: _parse_date(_first(d.get("_info"), "startUp", "startup")),
    },
    "software_version": {
        "name": "Software Version",
        "source": "_info",
        "entity_category": EntityCategory.DIAGNOSTIC,
        "value_fn": lambda d: _first(d.get("_info"), "swVersion", "softwareVersion"),
    },
    "last_error": {
        "name": "Last Error",
        "source": "_info",
        "value_fn": lambda d: _latest_error(d.get("_info")),
        "attributes_fn": lambda d: {"errors": (d.get("_info") or {}).get("errors")},
    },
    "raw_water_hardness": {
        "name": "Raw Water Hardness",
        "source": "_parameters",
        "unit": "°dH",
        "entity_category": EntityCategory.DIAGNOSTIC,
        "value_fn": lambda d: _first(d.get("_parameters"), "prawhard"),
    },
    "soft_water_hardness": {
        "name": "Soft Water Hardness Setpoint",
        "source": "_parameters",
        "unit": "°dH",
        "entity_category": EntityCategory.DIAGNOSTIC,
        "value_fn": lambda d: _first(d.get("_parameters"), "psetsoft"),
    },
    "regeneration_time": {
        "name": "Regeneration Time",
        "source": "_parameters",
        "entity_category": EntityCategory.DIAGNOSTIC,
        "value_fn": lambda d: _regeneration_times(d.get("_parameters")),
    },
    "maintenance_interval": {
        "name": "Maintenance Interval",
        "source": "_parameters",
        "unit": "d",
        "device_class": SensorDeviceClass.DURATION,
        "entity_category": EntityCategory.DIAGNOSTIC,
        "value_fn": lambda d: _first(d.get("_parameters"), "pmaintint"),
    },
    "nominal_flow": {
        "name": "Nominal Flow Rate",
        "source": "_parameters",
        "unit": "m³/h",
        "device_class": SensorDeviceClass.VOLUME_FLOW_RATE,
        "entity_category": EntityCategory.DIAGNOSTIC,
        "value_fn": lambda d: _first(d.get("_parameters"), "pnomflow"),
    },
    "water_yesterday": {
        "name": "Water Usage Yesterday (Cloud)",
        "source": "_water",
        "unit": "L",
        "device_class": SensorDeviceClass.WATER,
        "value_fn": lambda d: _yesterday_value(d.get("_water")),
        "attributes_fn": lambda d: {"daily": _recent_entries(d.get("_water"))},
    },
    "lime_retained_yesterday": {
        "name": "Lime Retained Yesterday (Cloud)",
        "source": "_water",
        "unit": "g",
        "device_class": SensorDeviceClass.WEIGHT,
        "value_fn": lambda d: _yesterday_value(d.get("_water"), "limeRetained"),
        "attributes_fn": lambda d: {
            "daily": _recent_entries(d.get("_water"), "limeRetained")
        },
    },
    "salt_yesterday": {
        "name": "Salt Usage Yesterday (Cloud)",
        "source": "_salt",
        "unit": "g",
        "device_class": SensorDeviceClass.WEIGHT,
        "value_fn": lambda d: _yesterday_value(d.get("_salt")),
        "attributes_fn": lambda d: {"daily": _recent_entries(d.get("_salt"))},
    },
    "salt_daily_sum": {
        "name": "Salt Usage Sum of Daily Values (Cloud)",
        "source": "_salt",
        "unit": "kg",
        "device_class": SensorDeviceClass.WEIGHT,
        "value_fn": lambda d: _sum_values(d.get("_salt"), 0.001),
        "attributes_fn": lambda d: {
            "days": len(d.get("_salt") or []),
            "first_day": min(
                (str(e.get("date"))[:10] for e in d.get("_salt") or [] if isinstance(e, dict)),
                default=None,
            ),
        },
    },
}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Grünbeck Cloud SE sensors."""
    coordinator: GruenbeckDataUpdateCoordinator = hass.data[DOMAIN][
        config_entry.entry_id
    ]

    entities: list[SensorEntity] = []

    # Add standard cloud polling sensors
    for key, info in SENSOR_TYPES.items():
        entities.append(
            GruenbeckCloudSensor(
                coordinator,
                key,
                info["name"],
                info["unit"],
                info["device_class"],
                info["state_class"],
                info.get("enabled_default", True),
            )
        )

    # Add exchanger 2 on devices that have one, and additional /update
    # fields reported by this device
    extra_types = dict(UPDATE_EXTRA_SENSOR_TYPES)
    if coordinator.features.second_exchanger:
        extra_types = {**SECOND_EXCHANGER_SENSOR_TYPES, **extra_types}
    registry = er.async_get(hass)
    for key, info in extra_types.items():
        if key not in coordinator.data:
            # Remove entities of fields this device does not report, e.g.
            # created by an earlier version that always added them
            if entity_id := registry.async_get_entity_id(
                "sensor", DOMAIN, f"{coordinator.device_id}_{key}"
            ):
                registry.async_remove(entity_id)
            continue
        entities.append(
            GruenbeckCloudSensor(
                coordinator,
                key,
                info["name"],
                info["unit"],
                info["device_class"],
                info["state_class"],
                info.get("enabled_default", True),
            )
        )

    # Add sensors from device info, parameters and daily measurements
    for key, info in CLOUD_SENSOR_TYPES.items():
        if coordinator.data.get(info["source"]) is None:
            continue
        entities.append(GruenbeckCloudDataSensor(coordinator, key, info))

    # Add the special calculated water consumption sensor
    entities.append(GruenbeckCalculatedWaterConsumptionSensor(coordinator))
    entities.append(GruenbeckAverageFlowSensor(coordinator))
    entities.append(GruenbeckDataLastChangedSensor(coordinator))
    entities.append(GruenbeckLastPollSensor(coordinator))
    entities.append(GruenbeckSettingChangesSensor(coordinator))
    entities.append(GruenbeckLastRegenerationSensor(coordinator))
    for kind in ("maintenance", "inspection"):
        entities.append(GruenbeckNextServiceSensor(coordinator, kind))
        entities.append(GruenbeckServiceDaysSensor(coordinator, kind))

    async_add_entities(entities)


class GruenbeckCloudSensor(GruenbeckEntity, SensorEntity):
    """Representation of a standard Grünbeck Cloud sensor."""

    def __init__(
        self,
        coordinator: GruenbeckDataUpdateCoordinator,
        entity_key: str,
        name: str,
        unit: str | None,
        device_class: SensorDeviceClass | None,
        state_class: SensorStateClass | None,
        enabled_default: bool = True,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entity_key)
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        self._attr_state_class = state_class
        self._attr_entity_registry_enabled_default = enabled_default

    @property
    def native_value(self) -> float | int | str | None:
        """Return the value reported by the sensor."""
        return self.coordinator.data.get(self.entity_key)


class GruenbeckCloudDataSensor(GruenbeckEntity, SensorEntity):
    """Sensor based on device info, parameters or daily measurements."""

    def __init__(
        self,
        coordinator: GruenbeckDataUpdateCoordinator,
        entity_key: str,
        info: dict[str, Any],
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entity_key)
        self._value_fn: Callable[[dict[str, Any]], Any] = info["value_fn"]
        self._attributes_fn: Callable[[dict[str, Any]], dict[str, Any]] | None = (
            info.get("attributes_fn")
        )
        self._attr_native_unit_of_measurement = info.get("unit")
        self._attr_device_class = info.get("device_class")
        self._attr_state_class = info.get("state_class")
        self._attr_entity_category = info.get("entity_category")
        self._attr_options = info.get("options")
        self._attr_entity_registry_enabled_default = info.get("enabled_default", True)

    @property
    def native_value(self) -> Any:
        """Return the value reported by the sensor."""
        return self._value_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return additional attributes."""
        attributes = super().extra_state_attributes or {}
        if self._attributes_fn is not None:
            attributes = {**attributes, **self._attributes_fn(self.coordinator.data)}
        return attributes or None


class GruenbeckCalculatedWaterConsumptionSensor(
    GruenbeckEntity, RestoreEntity, SensorEntity
):
    """Calculated total water consumption sensor using duplex remaining capacities."""

    _attr_device_class = SensorDeviceClass.WATER
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_native_unit_of_measurement = "L"

    def __init__(self, coordinator: GruenbeckDataUpdateCoordinator) -> None:
        """Initialize the calculated water consumption sensor."""
        super().__init__(coordinator, "calculated_water_consumption")
        self._state: float = 0.0
        self._last_cap1: float | None = None
        self._last_cap2: float | None = None
        self._store: Store | None = None
        self._restored: bool = False

    async def async_added_to_hass(self) -> None:
        """Call when entity is added to Home Assistant."""
        await super().async_added_to_hass()
        
        # Initialize the storage handler
        storage_key = f"{DOMAIN}_{self.coordinator.device_id}_water_consumption"
        self._store = Store(self.hass, 1, storage_key)
        
        # Try to load the state from both the store and RestoreEntity
        stored_state: float | None = None
        restored_state: float | None = None

        stored_data = await self._store.async_load()
        if stored_data is not None and "state" in stored_data:
            try:
                stored_state = float(stored_data["state"])
            except (ValueError, TypeError):
                pass

        if (state := await self.async_get_last_state()) is not None:
            if state.state not in ("unknown", "unavailable"):
                try:
                    restored_state = float(state.state)
                except (ValueError, TypeError):
                    pass

        # Select the maximum to ensure the total value never decreases
        possible_states = [s for s in (stored_state, restored_state) if s is not None]
        if possible_states:
            self._state = max(possible_states)
            # Save the resolved maximum immediately to the store
            await self._store.async_save({"state": self._state})
        else:
            self._state = 0.0

        self._restored = True
        self.async_write_ha_state()

    @property
    def native_value(self) -> float:
        """Return the state of the sensor."""
        return round(self._state, 1)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if not self._restored:
            return

        data = self.coordinator.data
        if not data:
            return

        current_cap1 = data.get("mrescapa1")
        current_cap2 = data.get("mRescapa2")
        state_changed = False

        # Exchanger 1 Delta calculation
        if current_cap1 is not None:
            try:
                current_cap1 = float(current_cap1)
                # Ignore 0.0 values (active regeneration or offline status)
                if current_cap1 > 0.0:
                    if self._last_cap1 is not None:
                        if current_cap1 < self._last_cap1:
                            self._state += self._last_cap1 - current_cap1
                            state_changed = True
                    self._last_cap1 = current_cap1
            except (ValueError, TypeError):
                pass

        # Exchanger 2 Delta calculation
        if current_cap2 is not None:
            try:
                current_cap2 = float(current_cap2)
                # Ignore 0.0 values (active regeneration or offline status)
                if current_cap2 > 0.0:
                    if self._last_cap2 is not None:
                        if current_cap2 < self._last_cap2:
                            self._state += self._last_cap2 - current_cap2
                            state_changed = True
                    self._last_cap2 = current_cap2
            except (ValueError, TypeError):
                pass

        self.async_write_ha_state()

        # Save to store if updated
        if state_changed and self._store is not None:
            self.hass.async_create_task(self._store.async_save({"state": self._state}))


class GruenbeckAverageFlowSensor(GruenbeckEntity, SensorEntity):
    """Average soft water flow between two polls, from capacity decreases."""

    _attr_device_class = SensorDeviceClass.VOLUME_FLOW_RATE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "L/min"

    def __init__(self, coordinator: GruenbeckDataUpdateCoordinator) -> None:
        """Initialize the average flow sensor."""
        super().__init__(coordinator, "average_flow_rate")
        self._last_caps: dict[str, float] = {}
        self._last_time: datetime | None = None
        self._value: float | None = None
        self._consumed: float | None = None

    @property
    def native_value(self) -> float | None:
        """Return the average flow in L/min."""
        return self._value

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the consumed volume and interval."""
        return {**(super().extra_state_attributes or {}), "consumed_liters": self._consumed}

    async def async_added_to_hass(self) -> None:
        """Use the data of the initial refresh as baseline."""
        await super().async_added_to_hass()
        self._calculate()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._calculate()
        self.async_write_ha_state()

    def _calculate(self) -> None:
        """Calculate the average flow since the previous poll."""
        data = self.coordinator.data or {}
        now = dt_util.utcnow()
        consumed = 0.0
        valid = False

        for key in ("mrescapa1", "mRescapa2"):
            try:
                current = float(data.get(key))
            except (TypeError, ValueError):
                continue
            # Ignore 0.0 values (active regeneration or offline status)
            if current <= 0.0:
                continue
            last = self._last_caps.get(key)
            if last is not None:
                valid = True
                # Increases are regenerations, not consumption
                if current < last:
                    consumed += last - current
            self._last_caps[key] = current

        if valid and self._last_time is not None:
            minutes = (now - self._last_time).total_seconds() / 60
            if minutes > 0:
                self._consumed = round(consumed, 1)
                self._value = round(consumed / minutes, 2)
        self._last_time = now


class GruenbeckDataLastChangedSensor(GruenbeckEntity, SensorEntity):
    """Time of the last change in the device data.

    If this does not change for hours although water is used, the cloud
    data is frozen (device error or rate limiting).
    """

    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: GruenbeckDataUpdateCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, "data_last_changed")

    @property
    def native_value(self) -> datetime | None:
        """Return the time of the last data change."""
        return self.coordinator.last_data_change


class GruenbeckLastPollSensor(GruenbeckEntity, SensorEntity):
    """Time of the last successful poll of the live telemetry."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: GruenbeckDataUpdateCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, "last_poll")

    @property
    def native_value(self) -> datetime | None:
        """Return the time of the last successful poll."""
        return self.coordinator.last_poll


class GruenbeckSettingChangesSensor(GruenbeckEntity, SensorEntity):
    """Time of the last changed setting, the changes as attribute.

    Helps to find out which cloud parameter belongs to an option in the app:
    change the option in the app, press "Fetch settings now" and look at
    the attribute.
    """

    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _unrecorded_attributes = frozenset({"description", "changes"})

    def __init__(self, coordinator: GruenbeckDataUpdateCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, "setting_changes")

    @property
    def native_value(self) -> datetime | None:
        """Return the time of the last recorded change."""
        changes = self.coordinator.setting_changes
        if not changes:
            return None
        return dt_util.parse_datetime(changes[0]["time"])

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return the last changes."""
        attributes = super().extra_state_attributes or {}
        return {
            **attributes,
            "changes": [
                f"{c['time'][:16].replace('T', ' ')} {c['key']}: {c['old']} → {c['new']}"
                for c in self.coordinator.setting_changes[:20]
            ],
        }


REGENERATION_HISTORY_SIZE = 20


class GruenbeckLastRegenerationSensor(GruenbeckEntity, RestoreEntity, SensorEntity):
    """Time of the last regeneration, detected from the regeneration counter.

    The cloud does not report this for the SE series, so the time is
    recorded when the counter increases (at polling resolution).
    """

    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, coordinator: GruenbeckDataUpdateCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, "last_regeneration")
        self._value: datetime | None = None
        self._last_count: int | None = None
        # Capacity seen at the last poll without regeneration
        self._last_capacity: tuple[Any, Any] | None = None
        self._history: list[dict[str, Any]] = []

    async def async_added_to_hass(self) -> None:
        """Restore the previous value and counter."""
        await super().async_added_to_hass()
        if (state := await self.async_get_last_state()) is not None:
            self._value = dt_util.parse_datetime(state.state)
            try:
                self._last_count = int(state.attributes.get("regeneration_count"))
            except (TypeError, ValueError):
                self._last_count = None
            history = state.attributes.get("history")
            if isinstance(history, list):
                self._history = history[-REGENERATION_HISTORY_SIZE:]
        self._check_counter()

    @property
    def native_value(self) -> datetime | None:
        """Return the time of the last regeneration."""
        return self._value

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the counter used for the detection."""
        return {
            **(super().extra_state_attributes or {}),
            "regeneration_count": self._last_count,
            "history": self._history,
        }

    def _check_counter(self) -> None:
        """Record time and capacity when the regeneration counter increases."""
        data = self.coordinator.data or {}
        try:
            count = int(data.get("mcountreg"))
        except (TypeError, ValueError):
            return
        if self._last_count is not None and count > self._last_count:
            self._value = dt_util.now()
            percent, liters = self._last_capacity or (None, None)
            self._history.append(
                {
                    "time": self._value.isoformat(timespec="minutes"),
                    "capacity_percent": percent,
                    "capacity_liters": liters,
                }
            )
            self._history = self._history[-REGENERATION_HISTORY_SIZE:]
        self._last_count = count

        # Remember the capacity before a regeneration starts
        try:
            regenerating = int(data.get("mregstatus") or 0) != 0
            liters = float(data.get("mrescapa1"))
        except (TypeError, ValueError):
            return
        if not regenerating and liters > 0:
            self._last_capacity = (data.get("mresidcap1"), liters)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._check_counter()
        self.async_write_ha_state()


class GruenbeckNextServiceSensor(GruenbeckEntity, SensorEntity):
    """Date of the next maintenance or inspection (last date + interval)."""

    _attr_device_class = SensorDeviceClass.DATE

    def __init__(self, coordinator: GruenbeckDataUpdateCoordinator, kind: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, f"next_{kind}")
        self._kind = kind

    @property
    def native_value(self) -> date | None:
        """Return the next service date."""
        return self.coordinator.next_service_date(self._kind)


class GruenbeckServiceDaysSensor(GruenbeckEntity, SensorEntity):
    """Days until the next maintenance or inspection, negative if overdue."""

    _attr_native_unit_of_measurement = "d"
    _attr_icon = "mdi:calendar-clock"

    def __init__(self, coordinator: GruenbeckDataUpdateCoordinator, kind: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, f"{kind}_days_remaining")
        self._kind = kind

    @property
    def native_value(self) -> int | None:
        """Return the remaining days."""
        next_date = self.coordinator.next_service_date(self._kind)
        if next_date is None:
            return None
        return (next_date - dt_util.now().date()).days
