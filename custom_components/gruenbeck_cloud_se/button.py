"""Support for Grünbeck Cloud SE buttons."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .coordinator import GruenbeckDataUpdateCoordinator
from .entity import GruenbeckEntity


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Grünbeck Cloud SE buttons."""
    coordinator: GruenbeckDataUpdateCoordinator = hass.data[DOMAIN][
        config_entry.entry_id
    ]
    async_add_entities(
        [
            GruenbeckServiceDoneButton(coordinator, "maintenance"),
            GruenbeckServiceDoneButton(coordinator, "inspection"),
            GruenbeckRefreshSettingsButton(coordinator),
        ]
    )


class GruenbeckServiceDoneButton(GruenbeckEntity, ButtonEntity):
    """Set the last maintenance or inspection date to today."""

    _attr_icon = "mdi:wrench-check"

    def __init__(self, coordinator: GruenbeckDataUpdateCoordinator, kind: str) -> None:
        """Initialize the button."""
        super().__init__(coordinator, f"{kind}_done")
        self._kind = kind

    @property
    def available(self) -> bool:
        """Local action, always available."""
        return True

    async def async_press(self) -> None:
        """Store today as last service date."""
        await self.coordinator.async_set_service_date(
            self._kind, dt_util.now().date()
        )


class GruenbeckRefreshSettingsButton(GruenbeckEntity, ButtonEntity):
    """Fetch device info and parameters now instead of waiting an hour."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:cloud-refresh"

    def __init__(self, coordinator: GruenbeckDataUpdateCoordinator) -> None:
        """Initialize the button."""
        super().__init__(coordinator, "refresh_settings")

    async def async_press(self) -> None:
        """Read the settings from the cloud."""
        await self.coordinator.async_refresh_settings()
