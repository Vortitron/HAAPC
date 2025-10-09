"""Switch platform for APC PDU."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import APCPDUDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up APC PDU switches."""
    coordinator: APCPDUDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    
    entities = []
    
    # Get outlet count from coordinator data
    outlets = coordinator.data.get("outlets", {})
    
    # Add individual outlet switches
    for outlet_num in outlets:
        entities.append(APCPDUOutletSwitch(coordinator, entry, outlet_num))
    
    # Add master switch
    entities.append(APCPDUMasterSwitch(coordinator, entry))
    
    async_add_entities(entities)


class APCPDUOutletSwitch(CoordinatorEntity[APCPDUDataUpdateCoordinator], SwitchEntity):
    """Representation of an APC PDU outlet switch."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: APCPDUDataUpdateCoordinator,
        entry: ConfigEntry,
        outlet_num: int,
    ) -> None:
        """Initialize the outlet switch."""
        super().__init__(coordinator)
        self.outlet_num = outlet_num
        self._entry = entry
        
        device_info = coordinator.data.get("device_info", {})
        serial = device_info.get("serial_number", entry.entry_id)
        
        self._attr_unique_id = f"{serial}_outlet_{outlet_num}"
        self._attr_name = f"Outlet {outlet_num}"
        
    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        device_data = self.coordinator.data.get("device_info", {})
        
        return DeviceInfo(
            identifiers={(DOMAIN, device_data.get("serial_number", self._entry.entry_id))},
            name=self._entry.data.get("name") or device_data.get("model", "APC PDU"),
            manufacturer="APC",
            model=device_data.get("model"),
            sw_version=device_data.get("firmware"),
            hw_version=device_data.get("hardware"),
        )

    @property
    def is_on(self) -> bool | None:
        """Return true if outlet is on."""
        outlet_data = self.coordinator.data.get("outlets", {}).get(self.outlet_num, {})
        return outlet_data.get("is_on")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        outlet_data = self.coordinator.data.get("outlets", {}).get(self.outlet_num, {})
        
        attrs = {
            "outlet_number": self.outlet_num,
            "outlet_name": outlet_data.get("name"),
        }
        
        # Add power if available
        power = outlet_data.get("power")
        if power is not None:
            attrs["power_w"] = power
        
        return attrs

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the outlet on."""
        success = await self.hass.async_add_executor_job(
            self.coordinator.client.set_outlet, self.outlet_num, True
        )
        
        if success:
            await self.coordinator.async_request_refresh()
        else:
            _LOGGER.error("Failed to turn on outlet %s", self.outlet_num)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the outlet off."""
        success = await self.hass.async_add_executor_job(
            self.coordinator.client.set_outlet, self.outlet_num, False
        )
        
        if success:
            await self.coordinator.async_request_refresh()
        else:
            _LOGGER.error("Failed to turn off outlet %s", self.outlet_num)


class APCPDUMasterSwitch(CoordinatorEntity[APCPDUDataUpdateCoordinator], SwitchEntity):
    """Representation of an APC PDU master switch (all outlets)."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: APCPDUDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the master switch."""
        super().__init__(coordinator)
        self._entry = entry
        
        device_info = coordinator.data.get("device_info", {})
        serial = device_info.get("serial_number", entry.entry_id)
        
        self._attr_unique_id = f"{serial}_master_switch"
        self._attr_name = "Master Switch"
        self._attr_icon = "mdi:power-plug"
        
    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        device_data = self.coordinator.data.get("device_info", {})
        
        return DeviceInfo(
            identifiers={(DOMAIN, device_data.get("serial_number", self._entry.entry_id))},
            name=self._entry.data.get("name") or device_data.get("model", "APC PDU"),
            manufacturer="APC",
            model=device_data.get("model"),
            sw_version=device_data.get("firmware"),
            hw_version=device_data.get("hardware"),
        )

    @property
    def is_on(self) -> bool | None:
        """Return true if any outlet is on."""
        outlets = self.coordinator.data.get("outlets", {})
        return any(outlet.get("is_on") for outlet in outlets.values())

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        outlets = self.coordinator.data.get("outlets", {})
        pdu_status = self.coordinator.data.get("pdu_status", {})
        
        total_power = sum(
            outlet.get("power", 0) or 0 for outlet in outlets.values()
        )
        
        outlets_on = sum(1 for outlet in outlets.values() if outlet.get("is_on"))
        
        attrs = {
            "total_outlets": len(outlets),
            "outlets_on": outlets_on,
            "total_power_w": total_power,
        }
        
        # Add PDU status info
        if pdu_status.get("rated_voltage"):
            attrs["rated_voltage"] = pdu_status["rated_voltage"]
        if pdu_status.get("rated_max_current"):
            attrs["rated_max_current"] = pdu_status["rated_max_current"]
        if pdu_status.get("bank_load_state"):
            attrs["bank_load_state"] = pdu_status["bank_load_state"]
        
        return attrs

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn all outlets on."""
        success = await self.hass.async_add_executor_job(
            self.coordinator.client.set_all_outlets, True
        )
        
        if success:
            await self.coordinator.async_request_refresh()
        else:
            _LOGGER.error("Failed to turn on all outlets")

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn all outlets off."""
        success = await self.hass.async_add_executor_job(
            self.coordinator.client.set_all_outlets, False
        )
        
        if success:
            await self.coordinator.async_request_refresh()
        else:
            _LOGGER.error("Failed to turn off all outlets")

