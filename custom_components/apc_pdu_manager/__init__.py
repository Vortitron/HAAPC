"""The APC PDU integration."""

from __future__ import annotations

import logging
import re
from datetime import timedelta

from homeassistant.const import CONF_HOST, CONF_PORT, CONF_SCAN_INTERVAL, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryError, ConfigEntryNotReady
from homeassistant.helpers import entity_registry as er

from .config_flow import OPTIONS_FLOW_RELOADS
from .const import (
    CONF_COMMUNITY,
    CONF_SNMP_VERSION,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SNMP_VERSION,
)
from .coordinator import APCPDUConfigEntry, APCPDUCoordinator, client_from_data
from .snmp import APCPDUError, CannotConnect, InvalidAuth

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.SWITCH]

# Entities created by 1.0.x that no longer exist (they duplicated device
# information or reported values under the wrong meaning or unit).
_LEGACY_UNIQUE_ID = re.compile(
    r"_(outlet_count|hardware|firmware|rated_max_current|outlet_\d+_power)$"
)


async def async_setup_entry(hass: HomeAssistant, entry: APCPDUConfigEntry) -> bool:
    """Set up an APC PDU from a config entry."""
    client = client_from_data(dict(entry.data))
    try:
        info = await client.async_get_info()
    except InvalidAuth as err:
        await client.async_close()
        raise ConfigEntryError(
            f"The PDU rejected the SNMPv3 credentials ({err}); reconfigure the entry"
        ) from err
    except CannotConnect as err:
        await client.async_close()
        raise ConfigEntryNotReady(f"No SNMP response from {entry.data[CONF_HOST]}") from err
    except APCPDUError as err:
        await client.async_close()
        raise ConfigEntryNotReady(str(err)) from err

    coordinator = APCPDUCoordinator(hass, entry, client, info)
    try:
        await coordinator.async_config_entry_first_refresh()
    except ConfigEntryNotReady:
        await client.async_close()
        raise

    entry.runtime_data = coordinator
    _remove_legacy_entities(hass, entry)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    if not OPTIONS_FLOW_RELOADS:
        entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: APCPDUConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        await entry.runtime_data.client.async_close()
    return unload_ok


async def _async_update_listener(hass: HomeAssistant, entry: APCPDUConfigEntry) -> None:
    """Apply a changed poll interval (Home Assistant before 2025.8 only)."""
    entry.runtime_data.update_interval = timedelta(
        seconds=entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    )


async def async_migrate_entry(hass: HomeAssistant, entry: APCPDUConfigEntry) -> bool:
    """Migrate entries created by 1.0.x."""
    if entry.version > 1:
        return False
    if entry.minor_version < 2:
        old = dict(entry.data)
        if old.get("demo_mode"):
            _LOGGER.warning(
                "Demo mode has been removed; %s will now be polled as a real PDU",
                entry.title,
            )
        data = {
            CONF_HOST: old[CONF_HOST],
            CONF_PORT: old.get(CONF_PORT, DEFAULT_PORT),
            CONF_SNMP_VERSION: old.get(CONF_SNMP_VERSION, DEFAULT_SNMP_VERSION),
            CONF_COMMUNITY: old.get(CONF_COMMUNITY, ""),
        }
        hass.config_entries.async_update_entry(entry, data=data, minor_version=2)
    return True


def _remove_legacy_entities(hass: HomeAssistant, entry: APCPDUConfigEntry) -> None:
    registry = er.async_get(hass)
    for entity in er.async_entries_for_config_entry(registry, entry.entry_id):
        if _LEGACY_UNIQUE_ID.search(entity.unique_id):
            registry.async_remove(entity.entity_id)
