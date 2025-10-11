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
from .snmp_cli_client import SNMPCLIClient
from .snmp_client import SNMPClient

_LOGGER = logging.getLogger(__name__)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""
    _LOGGER.warning(
        "=== APC PDU Connection Attempt === Host: %s, Community: %s, Version: %s, Demo: %s",
        data[CONF_HOST],
        data[CONF_COMMUNITY][:3] + "***",  # Partially hide community string
        data.get(CONF_SNMP_VERSION, DEFAULT_SNMP_VERSION),
        data.get(CONF_DEMO_MODE, False),
    )
    
    # Use demo client if demo mode is enabled
    if data.get(CONF_DEMO_MODE, False):
        _LOGGER.warning("Using Demo Mode (simulated PDU)")
        client = DemoSNMPClient(
            host=data[CONF_HOST],
            community=data[CONF_COMMUNITY],
            version=data.get(CONF_SNMP_VERSION, DEFAULT_SNMP_VERSION),
        )
    else:
        # Try pysnmp first (if HA's SNMP works, this should too!)
        # Then fall back to CLI if unavailable
        try:
            _LOGGER.warning("Attempting to use pysnmp library...")
            client = SNMPClient(
                host=data[CONF_HOST],
                community=data[CONF_COMMUNITY],
                version=data.get(CONF_SNMP_VERSION, DEFAULT_SNMP_VERSION),
            )
            _LOGGER.warning("✅ Successfully initialized pysnmp client")
        except ImportError as err:
            # pysnmp not available - try CLI fallback
            _LOGGER.warning(
                "⚠️ pysnmp not available (%s), trying command-line SNMP tools as fallback",
                err
            )
            try:
                client = SNMPCLIClient(
                    host=data[CONF_HOST],
                    community=data[CONF_COMMUNITY],
                    version=data.get(CONF_SNMP_VERSION, DEFAULT_SNMP_VERSION),
                )
                _LOGGER.warning("✅ Successfully initialized CLI SNMP client")
            except ImportError as cli_err:
                # CLI tools also not available
                _LOGGER.error(
                    "❌ Both pysnmp and CLI tools unavailable. "
                    "Original pysnmp error: %s. CLI error: %s. "
                    "Please enable Demo Mode for testing.",
                    err, cli_err
                )
                raise CannotConnect(
                    "SNMP not available. Both pysnmp and CLI tools failed. "
                    "Please enable Demo Mode or wait for Home Assistant to fix pysnmp."
                ) from cli_err
    
    # Test connection by getting device info
    _LOGGER.warning("Testing connection by retrieving device info...")
    try:
        device_info = await hass.async_add_executor_job(client.get_device_info)
        _LOGGER.warning("Device info retrieved: %s", device_info)
    except Exception as ex:
        _LOGGER.error("❌ Failed to get device info: %s (type: %s)", ex, type(ex).__name__, exc_info=True)
        raise CannotConnect(f"Unable to connect to PDU: {ex}") from ex
    
    if not device_info:
        _LOGGER.error("❌ Device info is None or empty")
        raise CannotConnect("Unable to get device information from PDU (no data returned)")
    
    if not device_info.get("model"):
        _LOGGER.error("❌ Device info missing 'model' field. Got: %s", device_info)
        raise CannotConnect("Unable to get device model from PDU")
    
    # Determine title
    title = data.get(CONF_NAME) or device_info.get("model") or "APC PDU"
    _LOGGER.warning("✅ Connection successful! Title: %s", title)
    
    return {
        "title": title,
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

