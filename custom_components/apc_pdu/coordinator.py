"""Polling coordinator for APC PDU."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_SCAN_INTERVAL, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    AUTH_NONE,
    CONF_AUTH_KEY,
    CONF_AUTH_PROTOCOL,
    CONF_COMMUNITY,
    CONF_PRIV_KEY,
    CONF_PRIV_PROTOCOL,
    CONF_SNMP_VERSION,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SNMP_VERSION,
    DOMAIN,
    PRIV_NONE,
)
from .snmp import APCPDUClient, APCPDUError, PDUInfo, PDUStatus, SNMPAuth

_LOGGER = logging.getLogger(__name__)

type APCPDUConfigEntry = ConfigEntry[APCPDUCoordinator]


def auth_from_data(data: dict[str, Any]) -> SNMPAuth:
    """Build SNMP credentials from config entry data."""
    return SNMPAuth(
        version=data.get(CONF_SNMP_VERSION, DEFAULT_SNMP_VERSION),
        community=data.get(CONF_COMMUNITY),
        username=data.get(CONF_USERNAME),
        auth_protocol=data.get(CONF_AUTH_PROTOCOL, AUTH_NONE),
        auth_key=data.get(CONF_AUTH_KEY),
        priv_protocol=data.get(CONF_PRIV_PROTOCOL, PRIV_NONE),
        priv_key=data.get(CONF_PRIV_KEY),
    )


def client_from_data(data: dict[str, Any]) -> APCPDUClient:
    """Create a client for config entry (or flow) data."""
    return APCPDUClient(
        data[CONF_HOST],
        auth_from_data(data),
        port=data.get(CONF_PORT, DEFAULT_PORT),
    )


class APCPDUCoordinator(DataUpdateCoordinator[PDUStatus]):
    """Polls one PDU."""

    config_entry: APCPDUConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        entry: APCPDUConfigEntry,
        client: APCPDUClient,
        info: PDUInfo,
    ) -> None:
        """Initialise the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=f"{DOMAIN} {entry.data[CONF_HOST]}",
            update_interval=timedelta(
                seconds=entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
            ),
        )
        self.client = client
        self.info = info

    async def _async_update_data(self) -> PDUStatus:
        try:
            return await self.client.async_get_status(self.info)
        except APCPDUError as err:
            raise UpdateFailed(f"Error polling PDU {self.client.host}: {err}") from err
