"""Base entity for Grünbeck Cloud SE Series."""
from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import GruenbeckDataUpdateCoordinator


class GruenbeckEntity(CoordinatorEntity[GruenbeckDataUpdateCoordinator]):
    """Base class for Grünbeck Cloud SE entities."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: GruenbeckDataUpdateCoordinator,
        entity_key: str,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self.entity_key = entity_key
        self._attr_unique_id = f"{coordinator.device_id}_{entity_key}"

        # Setup standard DeviceInfo
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.device_id)},
            name="Grünbeck SoftliQ SE",
            manufacturer="Grünbeck",
            model="softliQ.SE",
        )
