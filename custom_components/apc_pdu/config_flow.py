"""Config flow for APC PDU integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_validation as cv

from .const import (
    CONF_COMMUNITY,
    CONF_DEMO_MODE,
    CONF_NAME,
    CONF_SNMP_VERSION,
    DEFAULT_SNMP_VERSION,
    DOMAIN,
)
from .demo_client import DemoSNMPClient
from .snmp_client import SNMPClient

_LOGGER = logging.getLogger(__name__)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""
    # Use demo client if demo mode is enabled
    if data.get(CONF_DEMO_MODE, False):
        client = DemoSNMPClient(
            host=data[CONF_HOST],
            community=data[CONF_COMMUNITY],
            version=data.get(CONF_SNMP_VERSION, DEFAULT_SNMP_VERSION),
        )
    else:
        try:
            client = SNMPClient(
                host=data[CONF_HOST],
                community=data[CONF_COMMUNITY],
                version=data.get(CONF_SNMP_VERSION, DEFAULT_SNMP_VERSION),
            )
        except ImportError as err:
            # pysnmp not available - likely HA 2024.10.x issue
            raise CannotConnect(
                f"SNMP libraries not available. This is a known issue with Home Assistant 2024.10.x. "
                f"Please enable Demo Mode to test, or see FIX_HA_2024_10_SNMP.md for solutions. Error: {err}"
            ) from err
    
    # Test connection by getting device info
    device_info = await hass.async_add_executor_job(client.get_device_info)
    
    if not device_info:
        raise CannotConnect("Unable to connect to PDU")
    
    return {
        "title": data.get(CONF_NAME) or device_info.get("model", "APC PDU"),
        "device_info": device_info,
    }


class APCPDUConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for APC PDU."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                # Create unique ID from serial number if available
                device_info = info.get("device_info", {})
                unique_id = device_info.get("serial_number")
                
                if unique_id:
                    await self.async_set_unique_id(unique_id)
                    self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=info["title"],
                    data=user_input,
                )

        data_schema = vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                vol.Required(CONF_COMMUNITY, default="private"): str,
                vol.Optional(CONF_NAME): str,
                vol.Optional(CONF_SNMP_VERSION, default=DEFAULT_SNMP_VERSION): vol.In(
                    ["1", "2c"]
                ),
                vol.Optional(CONF_DEMO_MODE, default=False): bool,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )


class CannotConnect(Exception):
    """Error to indicate we cannot connect."""

