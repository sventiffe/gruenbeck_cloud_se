"""Config flow for Grünbeck Cloud SE Series integration."""
from __future__ import annotations

from typing import Any
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from pygruenbeck_cloud import PyGruenbeckCloud

from .const import DOMAIN, CONF_DEVICE_ID, LOGGER, CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL


class GruenbeckFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Grünbeck Cloud SE."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the flow."""
        self.username: str | None = None
        self.password: str | None = None
        self.devices: list[Any] = []

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self.username = user_input[CONF_USERNAME]
            self.password = user_input[CONF_PASSWORD]

            # Validate credentials by trying to login
            gb = PyGruenbeckCloud(self.username, self.password)
            try:
                success = await gb.login()
                if not success:
                    errors["base"] = "invalid_auth"
                else:
                    # Fetch devices
                    self.devices = await gb.get_devices()
                    if not self.devices:
                        errors["base"] = "no_devices"
                    else:
                        # Proceed to device selection step
                        return await self.async_step_device()
            except Exception as err:  # pylint: disable=broad-except
                LOGGER.exception("Unexpected exception during login: %s", err)
                errors["base"] = "cannot_connect"
            finally:
                if gb.session:
                    await gb.close()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_USERNAME): str,
                    vol.Required(CONF_PASSWORD): str,
                }
            ),
            errors=errors,
        )

    async def async_step_device(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle device selection."""
        errors: dict[str, str] = {}

        if user_input is not None:
            device_id = user_input[CONF_DEVICE_ID]

            # Check if this device is already configured
            await self.async_set_unique_id(device_id)
            self._abort_if_unique_id_configured()

            # Find selected device
            selected_device = next(
                (d for d in self.devices if d.id == device_id), None
            )
            title = selected_device.name if selected_device else device_id

            return self.async_create_entry(
                title=title,
                data={
                    CONF_USERNAME: self.username,
                    CONF_PASSWORD: self.password,
                    CONF_DEVICE_ID: device_id,
                },
                options={
                    CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
                },
            )

        # Build dropdown options
        device_options = {
            device.id: f"{device.name} ({device.series} - {device.id})"
            for device in self.devices
        }

        return self.async_show_form(
            step_id="device",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_DEVICE_ID,
                        default=list(device_options.keys())[0]
                        if device_options
                        else None,
                    ): vol.In(device_options),
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return GruenbeckOptionsFlowHandler(config_entry)


class GruenbeckOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Grünbeck Cloud SE."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        errors: dict[str, str] = {}

        if user_input is not None:
            new_password = user_input.get(CONF_PASSWORD, self.config_entry.data.get(CONF_PASSWORD))
            new_scan_interval = user_input.get(CONF_SCAN_INTERVAL, self.config_entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL))

            # Validate polling interval
            if new_scan_interval < 10:
                errors["base"] = "invalid_scan_interval"
            else:
                # Validate new credentials by trying to login if password changed
                if new_password != self.config_entry.data.get(CONF_PASSWORD):
                    gb = PyGruenbeckCloud(self.config_entry.data.get(CONF_USERNAME), new_password)
                    try:
                        success = await gb.login()
                        if not success:
                            errors["base"] = "invalid_auth"
                    except Exception:
                        errors["base"] = "cannot_connect"
                    finally:
                        if gb.session:
                            await gb.close()

                if not errors:
                    # Update config entry data for password
                    new_data = dict(self.config_entry.data)
                    new_data[CONF_PASSWORD] = new_password
                    self.hass.config_entries.async_update_entry(
                        self.config_entry, data=new_data
                    )

                    # Save scan interval in options
                    return self.async_create_entry(
                        title="",
                        data={
                            CONF_SCAN_INTERVAL: new_scan_interval,
                        },
                    )

        # Current values
        current_password = self.config_entry.data.get(CONF_PASSWORD)
        current_scan_interval = self.config_entry.options.get(
            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
        )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_PASSWORD, default=current_password
                    ): str,
                    vol.Required(
                        CONF_SCAN_INTERVAL, default=current_scan_interval
                    ): int,
                }
            ),
            errors=errors,
        )
