"""Support for Grünbeck Cloud SE binary sensors."""
from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import GruenbeckDataUpdateCoordinator
from .entity import GruenbeckEntity


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Grünbeck Cloud SE binary sensors."""
    coordinator: GruenbeckDataUpdateCoordinator = hass.data[DOMAIN][
        config_entry.entry_id
    ]

    entities = [
        GruenbeckErrorBinarySensor(coordinator),
        GruenbeckSaltWarningBinarySensor(coordinator),
    ]

    async_add_entities(entities)


class GruenbeckErrorBinarySensor(GruenbeckEntity, BinarySensorEntity):
    """Binary sensor for Grünbeck device error state."""

    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_name = "Device Error"

    def __init__(self, coordinator: GruenbeckDataUpdateCoordinator) -> None:
        """Initialize the error sensor."""
        super().__init__(coordinator, "has_error")

    @property
    def is_on(self) -> bool | None:
        """Return true if the device is in an error state."""
        return self.coordinator.data.get("hasError")


class GruenbeckSaltWarningBinarySensor(GruenbeckEntity, BinarySensorEntity):
    """Binary sensor for Grünbeck salt range warning."""

    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_name = "Salt Warning"

    def __init__(self, coordinator: GruenbeckDataUpdateCoordinator) -> None:
        """Initialize the salt warning sensor."""
        super().__init__(coordinator, "salt_warning")

    @property
    def is_on(self) -> bool | None:
        """Return true if there is a salt range issue."""
        val = self.coordinator.data.get("msaltrange")
        if val is None:
            return None
        # If it is a boolean, True usually means OK. So problem (is_on) = not OK.
        if isinstance(val, bool):
            return not val
        return False
