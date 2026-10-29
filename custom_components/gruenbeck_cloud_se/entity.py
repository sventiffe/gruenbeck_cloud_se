"""Base entity for Grünbeck Cloud SE Series."""
from __future__ import annotations

from typing import Any

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import GruenbeckDataUpdateCoordinator
from .descriptions import get_description

# Entities are grouped into sub-devices, everything else stays on the main
# device ("operation").
ENTITY_GROUPS = {
    "consumption": {
        "calculated_water_consumption",
        "average_flow_rate",
        "msaltusage",
        "mcountwater1",
        "mcountwater2",
        "mcountwatertank",
    },
    "daily": {
        "water_yesterday",
        "lime_retained_yesterday",
        "salt_yesterday",
        "salt_daily_sum",
    },
    "maintenance": {
        "last_maintenance",
        "last_inspection",
        "maintenance_done",
        "inspection_done",
        "next_maintenance",
        "next_inspection",
        "maintenance_days_remaining",
        "inspection_days_remaining",
        "maintenance_interval",
    },
    "settings": {
        "raw_water_hardness",
        "soft_water_hardness",
        "regeneration_time",
        "nominal_flow",
        "iq_mode",
        "led_brightness",
        "led_ring_permanent",
        "led_ring_failure",
        "led_ring_message",
        "led_ring_flow",
        "buzzer",
        "track_regeneration",
        "mcapacity",
    },
}


class GruenbeckEntity(CoordinatorEntity[GruenbeckDataUpdateCoordinator]):
    """Base class for Grünbeck Cloud SE entities."""

    _attr_has_entity_name = True
    # Static text, no need to store it in the history
    _unrecorded_attributes = frozenset({"description"})

    def __init__(
        self,
        coordinator: GruenbeckDataUpdateCoordinator,
        entity_key: str,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self.entity_key = entity_key
        self._attr_unique_id = f"{coordinator.device_id}_{entity_key}"
        # Names come from translations/<language>.json
        self._attr_translation_key = entity_key.lower()

        group = next(
            (g for g, keys in ENTITY_GROUPS.items() if entity_key in keys), None
        )
        if group is not None:
            self._attr_device_info = DeviceInfo(
                identifiers={(DOMAIN, f"{coordinator.device_id}_{group}")},
                translation_key=group,
                manufacturer="Grünbeck",
            )
            return

        # Setup standard DeviceInfo, enriched with the device info endpoint
        info = (coordinator.data or {}).get("_info") or {}
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.device_id)},
            name="Grünbeck SoftliQ SE",
            manufacturer="Grünbeck",
            model=coordinator.features.model,
            sw_version=info.get("swVersion"),
            hw_version=info.get("hwVersionCl"),
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return the description in the language of Home Assistant."""
        description = get_description(self.entity_key, self.hass.config.language)
        if description is None:
            return None
        return {"description": description}
