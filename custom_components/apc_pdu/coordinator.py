"""DataUpdateCoordinator for APC PDU."""
from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_COMMUNITY,
    CONF_DEMO_MODE,
    CONF_SNMP_VERSION,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SNMP_VERSION,
    DOMAIN,
)
from .demo_client import DemoSNMPClient
from .snmp_client import SNMPClient

_LOGGER = logging.getLogger(__name__)


class APCPDUDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching APC PDU data."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize."""
        self.entry = entry
        
        # Use demo client if demo mode is enabled
        if entry.data.get(CONF_DEMO_MODE, False):
            self.client = DemoSNMPClient(
                host=entry.data[CONF_HOST],
                community=entry.data[CONF_COMMUNITY],
                version=entry.data.get(CONF_SNMP_VERSION, DEFAULT_SNMP_VERSION),
            )
        else:
            self.client = SNMPClient(
                host=entry.data[CONF_HOST],
                community=entry.data[CONF_COMMUNITY],
                version=entry.data.get(CONF_SNMP_VERSION, DEFAULT_SNMP_VERSION),
            )
        
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{entry.entry_id}",
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Update data via SNMP."""
        try:
            device_info = await self.hass.async_add_executor_job(
                self.client.get_device_info
            )
            pdu_status = await self.hass.async_add_executor_job(
                self.client.get_pdu_status
            )
            outlets = await self.hass.async_add_executor_job(
                self.client.get_all_outlets_status
            )
            
            return {
                "device_info": device_info,
                "pdu_status": pdu_status,
                "outlets": outlets,
            }
        except Exception as ex:
            raise UpdateFailed(f"Error communicating with PDU: {ex}") from ex

