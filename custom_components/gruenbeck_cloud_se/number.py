"""Support for Grünbeck Cloud SE numbers."""
from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, EntityCategory
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
    """Set up Grünbeck Cloud SE numbers."""
    coordinator: GruenbeckDataUpdateCoordinator = hass.data[DOMAIN][
        config_entry.entry_id
    ]
    if (
        not coordinator.features.led_ring
        or (coordinator.data.get("_parameters") or {}).get("pledbright") is None
    ):
        return
    async_add_entities([GruenbeckLedBrightnessNumber(coordinator)])


class GruenbeckLedBrightnessNumber(GruenbeckEntity, NumberEntity):
    """Brightness of the illuminated LED ring."""

    _attr_entity_category = EntityCategory.CONFIG
    _attr_native_min_value = 0
    _attr_native_max_value = 100
    _attr_native_step = 10
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_mode = NumberMode.SLIDER
    _attr_icon = "mdi:led-on"

    def __init__(self, coordinator: GruenbeckDataUpdateCoordinator) -> None:
        """Initialize the number."""
        super().__init__(coordinator, "led_brightness")

    @property
    def native_value(self) -> float | None:
        """Return the LED brightness."""
        return (self.coordinator.data.get("_parameters") or {}).get("pledbright")

    async def async_set_native_value(self, value: float) -> None:
        """Set the LED brightness."""
        await self.coordinator.async_set_parameter("pledbright", int(value))
