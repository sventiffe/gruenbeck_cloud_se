"""Config flow for Grünbeck Cloud SE Series integration."""
from __future__ import annotations

from typing import Any
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.data_entry_flow import FlowResult
from pygruenbeck_cloud import PyGruenbeckCloud

from .const import DOMAIN, CONF_DEVICE_ID, LOGGER


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
