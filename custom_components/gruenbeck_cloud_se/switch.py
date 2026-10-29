"""Support for Grünbeck Cloud SE switches."""
from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_ON, EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DOMAIN, LED_RING_LEVELS, LED_RING_OFF, LED_RING_PERMANENT
from .coordinator import GruenbeckDataUpdateCoordinator
from .entity import GruenbeckEntity


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Grünbeck Cloud SE switches."""
    coordinator: GruenbeckDataUpdateCoordinator = hass.data[DOMAIN][
        config_entry.entry_id
    ]
    async_add_entities(
        [
            GruenbeckLiveModeSwitch(coordinator),
            GruenbeckTrackRegenerationSwitch(coordinator),
        ]
    )
    if (coordinator.data.get("_parameters") or {}).get("pbuzzer") is not None:
        async_add_entities([GruenbeckBuzzerSwitch(coordinator)])
    if (
        coordinator.features.led_ring
        and (coordinator.data.get("_parameters") or {}).get("pled") is not None
    ):
        async_add_entities(
            [GruenbeckLedRingPermanentSwitch(coordinator)]
            + [GruenbeckLedRingLevelSwitch(coordinator, key) for key in LED_RING_LEVELS]
        )
    if (coordinator.data.get("_parameters") or {}).get("pregmode") is not None:
        async_add_entities([GruenbeckIqModeSwitch(coordinator)])


class GruenbeckLiveModeSwitch(GruenbeckEntity, SwitchEntity):
    """Poll every 30 seconds for 5 minutes, then switch off automatically."""

    _attr_icon = "mdi:timer-sand"

    def __init__(self, coordinator: GruenbeckDataUpdateCoordinator) -> None:
        """Initialize the switch."""
        super().__init__(coordinator, "live_mode")

    @property
    def available(self) -> bool:
        """Keep the switch usable even if the last poll failed."""
        return True

    @property
    def is_on(self) -> bool:
        """Return True while live mode is active."""
        return self.coordinator.live_mode

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Start live mode."""
        await self.coordinator.async_start_live_mode()
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Stop live mode."""
        await self.coordinator.async_stop_live_mode()
        self.async_write_ha_state()


class GruenbeckTrackRegenerationSwitch(GruenbeckEntity, RestoreEntity, SwitchEntity):
    """Poll every minute while a regeneration is running (max. 60 minutes)."""

    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:magnify-scan"

    def __init__(self, coordinator: GruenbeckDataUpdateCoordinator) -> None:
        """Initialize the switch."""
        super().__init__(coordinator, "track_regeneration")

    async def async_added_to_hass(self) -> None:
        """Restore the previous state."""
        await super().async_added_to_hass()
        if (state := await self.async_get_last_state()) is not None:
            self.coordinator.track_regeneration = state.state == STATE_ON

    @property
    def available(self) -> bool:
        """Keep the switch usable even if the last poll failed."""
        return True

    @property
    def is_on(self) -> bool:
        """Return True if regeneration tracking is enabled."""
        return self.coordinator.track_regeneration

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Enable regeneration tracking."""
        self.coordinator.track_regeneration = True
        self.coordinator._apply_interval()
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Disable regeneration tracking."""
        self.coordinator.track_regeneration = False
        self.coordinator._apply_interval()
        self.async_write_ha_state()


class GruenbeckBuzzerSwitch(GruenbeckEntity, SwitchEntity):
    """Acoustic signal of the device on errors ("Signal bei Störung")."""

    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:bell-alert"

    def __init__(self, coordinator: GruenbeckDataUpdateCoordinator) -> None:
        """Initialize the switch."""
        super().__init__(coordinator, "buzzer")

    @property
    def is_on(self) -> bool | None:
        """Return True if the signal is enabled."""
        value = (self.coordinator.data.get("_parameters") or {}).get("pbuzzer")
        return None if value is None else bool(value)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Enable the signal."""
        await self.coordinator.async_set_parameter("pbuzzer", True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Disable the signal."""
        await self.coordinator.async_set_parameter("pbuzzer", False)


class GruenbeckIqModeSwitch(GruenbeckEntity, SwitchEntity):
    """iQ-Mode: the device chooses the regeneration time itself.

    Stored as regeneration mode: False/0 = automatic (iQ), True/1 = fixed time.
    """

    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:brain"

    def __init__(self, coordinator: GruenbeckDataUpdateCoordinator) -> None:
        """Initialize the switch."""
        super().__init__(coordinator, "iq_mode")

    @property
    def is_on(self) -> bool | None:
        """Return True if the regeneration time is chosen automatically."""
        value = (self.coordinator.data.get("_parameters") or {}).get("pregmode")
        return None if value is None else not bool(value)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Let the device choose the regeneration time."""
        await self.coordinator.async_set_parameter("pregmode", False)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Regenerate at the fixed times only."""
        await self.coordinator.async_set_parameter("pregmode", True)


class GruenbeckLedRingSwitch(GruenbeckEntity, SwitchEntity):
    """Base class for the LED ring switches, all stored in pled."""

    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:circle-outline"

    @property
    def _led(self) -> int | None:
        value = (self.coordinator.data.get("_parameters") or {}).get("pled")
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return the raw value as well."""
        return {**(super().extra_state_attributes or {}), "raw_value": self._led}


class GruenbeckLedRingPermanentSwitch(GruenbeckLedRingSwitch):
    """LED ring permanently on. Switches the other options off."""

    def __init__(self, coordinator: GruenbeckDataUpdateCoordinator) -> None:
        """Initialize the switch."""
        super().__init__(coordinator, "led_ring_permanent")

    @property
    def is_on(self) -> bool | None:
        """Return True if the LED ring is permanently on."""
        led = self._led
        return None if led is None else led == LED_RING_PERMANENT

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Light the LED ring permanently."""
        await self.coordinator.async_set_parameter("pled", LED_RING_PERMANENT)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Switch the LED ring off."""
        if self._led == LED_RING_PERMANENT:
            await self.coordinator.async_set_parameter("pled", LED_RING_OFF)


class GruenbeckLedRingLevelSwitch(GruenbeckLedRingSwitch):
    """LED ring on failure, message or flow.

    Each level includes the ones before it: switching on "flow" also
    switches on "message" and "failure", switching off "failure" also
    switches off the others.
    """

    def __init__(self, coordinator: GruenbeckDataUpdateCoordinator, key: str) -> None:
        """Initialize the switch."""
        super().__init__(coordinator, key)
        levels = list(LED_RING_LEVELS.values())
        self._level = LED_RING_LEVELS[key]
        index = levels.index(self._level)
        self._lower = levels[index - 1] if index else LED_RING_OFF

    @property
    def is_on(self) -> bool | None:
        """Return True if this level is active."""
        led = self._led
        if led is None:
            return None
        return led != LED_RING_PERMANENT and led >= self._level

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Activate this level (and the ones before it)."""
        led = self._led or LED_RING_OFF
        if led == LED_RING_PERMANENT or led < self._level:
            await self.coordinator.async_set_parameter("pled", self._level)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Deactivate this level (and the ones after it)."""
        led = self._led or LED_RING_OFF
        if led != LED_RING_PERMANENT and led >= self._level:
            await self.coordinator.async_set_parameter("pled", self._lower)
