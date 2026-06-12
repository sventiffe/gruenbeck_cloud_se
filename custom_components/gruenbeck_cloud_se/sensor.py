"""Support for Grünbeck Cloud SE sensors."""
from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.storage import Store

from .const import DOMAIN
from .coordinator import GruenbeckDataUpdateCoordinator
from .entity import GruenbeckEntity

SENSOR_TYPES = {
    "mrescapa1": {
        "name": "Exchanger 1 Remaining Capacity",
        "unit": "L",
        "device_class": SensorDeviceClass.VOLUME,
        "state_class": None,
    },
    "mRescapa2": {
        "name": "Exchanger 2 Remaining Capacity",
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
    "mresidcap2": {
        "name": "Exchanger 2 Remaining Capacity Percent",
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
        "unit": "m³/h",
        "device_class": SensorDeviceClass.VOLUME_FLOW_RATE,
        "state_class": SensorStateClass.MEASUREMENT,
        "enabled_default": False,
    },
    "mflow2": {
        "name": "Exchanger 2 Flow Rate",
        "unit": "m³/h",
        "device_class": SensorDeviceClass.VOLUME_FLOW_RATE,
        "state_class": SensorStateClass.MEASUREMENT,
        "enabled_default": False,
    },
    "mflowblend": {
        "name": "Blended Flow Rate",
        "unit": "m³/h",
        "device_class": SensorDeviceClass.VOLUME_FLOW_RATE,
        "state_class": SensorStateClass.MEASUREMENT,
        "enabled_default": False,
    },
    "mregstatus": {
        "name": "Regeneration Status",
        "unit": None,
        "device_class": None,
        "state_class": SensorStateClass.MEASUREMENT,
        "enabled_default": False,
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

    # Add the special calculated water consumption sensor
    entities.append(GruenbeckCalculatedWaterConsumptionSensor(coordinator))

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
        self._attr_name = name
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        self._attr_state_class = state_class
        self._attr_entity_registry_enabled_default = enabled_default

    @property
    def native_value(self) -> float | int | str | None:
        """Return the value reported by the sensor."""
        return self.coordinator.data.get(self.entity_key)


class GruenbeckCalculatedWaterConsumptionSensor(
    GruenbeckEntity, RestoreEntity, SensorEntity
):
    """Calculated total water consumption sensor using duplex remaining capacities."""

    _attr_device_class = SensorDeviceClass.WATER
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_native_unit_of_measurement = "L"
    _attr_name = "Calculated Water Consumption"

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
