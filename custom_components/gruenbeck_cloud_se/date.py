"""Support for Grünbeck Cloud SE dates."""
from __future__ import annotations

from datetime import date

from homeassistant.components.date import DateEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
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
    """Set up Grünbeck Cloud SE dates."""
    coordinator: GruenbeckDataUpdateCoordinator = hass.data[DOMAIN][
        config_entry.entry_id
    ]
    async_add_entities(
        [
            GruenbeckLastServiceDate(coordinator, "maintenance"),
            GruenbeckLastServiceDate(coordinator, "inspection"),
        ]
    )


class GruenbeckLastServiceDate(GruenbeckEntity, DateEntity):
    """Date of the last maintenance or inspection, editable by the user."""

    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator: GruenbeckDataUpdateCoordinator, kind: str) -> None:
        """Initialize the date."""
        super().__init__(coordinator, f"last_{kind}")
        self._kind = kind

    @property
    def available(self) -> bool:
        """Locally stored value, always available."""
        return True

    @property
    def native_value(self) -> date | None:
        """Return the last service date (start-up date as fallback)."""
        return self.coordinator.last_service_date(self._kind)

    async def async_set_value(self, value: date) -> None:
        """Change the last service date."""
        await self.coordinator.async_set_service_date(self._kind, value)
