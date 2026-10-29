"""The Grünbeck Cloud SE Series integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er
from pygruenbeck_cloud import PyGruenbeckCloud

from .const import CONF_DEVICE_ID, DOMAIN, LOGGER, CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
from .coordinator import GruenbeckDataUpdateCoordinator
from .entity import ENTITY_GROUPS

# Exchanger 2 entities of earlier versions, removed on single exchanger
# devices (softliQ SE) only
SECOND_EXCHANGER_ENTITIES = {
    ("sensor", "mRescapa2"),
    ("sensor", "mresidcap2"),
    ("sensor", "mflow2"),
    ("sensor", "mflowblend"),
}

# Entities of earlier versions that no longer exist: (platform, key)
OBSOLETE_ENTITIES = {
    ("sensor", "mregpercent2"),
    ("sensor", "mreswatadmod"),
    ("sensor", "mlime"),
    ("sensor", "water_today"),
    ("sensor", "salt_today"),
    ("sensor", "operation_mode"),
    ("button", "regenerate"),  # unsupported on the SE series
    ("sensor", "next_regeneration"),
    # Eco/Comfort/Power do not exist on the SE series, replaced by iQ-Mode
    ("select", "operation_mode"),
    # LED ring raw value sensor (local10) and select (local11), now switches
    ("sensor", "led_ring_mode"),
    ("select", "led_ring_mode"),
}

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.NUMBER,
    Platform.SWITCH,
    Platform.DATE,
    Platform.BUTTON,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Grünbeck Cloud SE from a config entry."""
    username = entry.data[CONF_USERNAME]
    password = entry.data[CONF_PASSWORD]
    device_id = entry.data[CONF_DEVICE_ID]

    # Create PyGruenbeckCloud API instance
    api = PyGruenbeckCloud(username, password)

    # Perform initial login to authenticate and verify session is working
    try:
        await api.login()
    except Exception as err:
        LOGGER.error(
            "Failed to login to Grünbeck Cloud during initialization: %s", err
        )
        raise

    # Get scan interval from options, falling back to default
    scan_interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

    # Create DataUpdateCoordinator
    coordinator = GruenbeckDataUpdateCoordinator(
        hass, api, device_id, scan_interval
    )

    await coordinator.async_load_service_dates()
    await coordinator.async_load_setting_changes()

    # Fetch initial data before completing setup
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    _async_remove_obsolete_entities(hass, entry, device_id)

    # Register the main device first, the group devices refer to it
    info = (coordinator.data or {}).get("_info") or {}
    device_registry = dr.async_get(hass)
    main_device = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, device_id)},
        name="Grünbeck SoftliQ SE",
        manufacturer="Grünbeck",
        model=coordinator.features.model,
        sw_version=info.get("swVersion"),
        hw_version=info.get("hwVersionCl"),
    )
    # Link the group devices to the main device. Done here with the device
    # id instead of via_device in DeviceInfo, which newer Home Assistant
    # versions deprecate.
    for group in ENTITY_GROUPS:
        group_device = device_registry.async_get_or_create(
            config_entry_id=entry.entry_id,
            identifiers={(DOMAIN, f"{device_id}_{group}")},
            translation_key=group,
            manufacturer="Grünbeck",
        )
        if group_device.via_device_id != main_device.id:
            device_registry.async_update_device(
                group_device.id, via_device_id=main_device.id
            )

    # Set up all platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register update listener to update options
    entry.async_on_unload(entry.add_update_listener(update_listener))

    return True


def _async_remove_obsolete_entities(
    hass: HomeAssistant, entry: ConfigEntry, device_id: str
) -> None:
    """Remove entities that were dropped in newer versions."""
    registry = er.async_get(hass)
    removed = set(OBSOLETE_ENTITIES)
    if not hass.data[DOMAIN][entry.entry_id].features.second_exchanger:
        removed |= SECOND_EXCHANGER_ENTITIES
    obsolete = {(platform, f"{device_id}_{key}") for platform, key in removed}
    for entity in er.async_entries_for_config_entry(registry, entry.entry_id):
        if (entity.domain, entity.unique_id) in obsolete:
            LOGGER.info("Removing obsolete entity %s", entity.entity_id)
            registry.async_remove(entity.entity_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(
        entry, PLATFORMS
    ):
        coordinator: GruenbeckDataUpdateCoordinator = hass.data[DOMAIN].pop(
            entry.entry_id
        )
        await coordinator.async_shutdown_live_mode()
        if coordinator.api.session:
            await coordinator.api.close()

    return unload_ok


async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)

