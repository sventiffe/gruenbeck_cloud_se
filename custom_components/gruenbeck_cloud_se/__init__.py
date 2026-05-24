"""The Grünbeck Cloud SE Series integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant
from pygruenbeck_cloud import PyGruenbeckCloud

from .const import CONF_DEVICE_ID, DOMAIN, LOGGER, CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
from .coordinator import GruenbeckDataUpdateCoordinator

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR]


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

    # Fetch initial data before completing setup
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    # Set up all platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register update listener to update options
    entry.async_on_unload(entry.add_update_listener(update_listener))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(
        entry, PLATFORMS
    ):
        coordinator: GruenbeckDataUpdateCoordinator = hass.data[DOMAIN].pop(
            entry.entry_id
        )
        if coordinator.api.session:
            await coordinator.api.close()

    return unload_ok


async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)

