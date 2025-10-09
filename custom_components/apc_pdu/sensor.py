"""Sensor platform for APC PDU."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfElectricCurrent, UnitOfElectricPotential, UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
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
    """Set up APC PDU sensors."""
    coordinator: APCPDUDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    
    entities = []
    
    # Add device info sensors
    entities.extend([
        APCPDUInfoSensor(coordinator, entry, "outlet_count", "Outlet Count", "mdi:power-socket"),
        APCPDUInfoSensor(coordinator, entry, "hardware", "Hardware Version", "mdi:chip", entity_category=EntityCategory.DIAGNOSTIC),
        APCPDUInfoSensor(coordinator, entry, "firmware", "Firmware Version", "mdi:package", entity_category=EntityCategory.DIAGNOSTIC),
    ])
    
    # Add PDU status sensors
    entities.extend([
        APCPDURatedVoltageSensor(coordinator, entry),
        APCPDURatedCurrentSensor(coordinator, entry),
        APCPDUBankLoadSensor(coordinator, entry),
    ])
    
    # Add per-outlet power sensors
    outlets = coordinator.data.get("outlets", {})
    for outlet_num in outlets:
        entities.append(APCPDUOutletPowerSensor(coordinator, entry, outlet_num))
    
    async_add_entities(entities)


class APCPDUInfoSensor(CoordinatorEntity[APCPDUDataUpdateCoordinator], SensorEntity):
    """Sensor for device information."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: APCPDUDataUpdateCoordinator,
        entry: ConfigEntry,
        info_key: str,
        name: str,
        icon: str,
        entity_category: EntityCategory | None = None,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._entry = entry
        self._info_key = info_key
        
        device_info = coordinator.data.get("device_info", {})
        serial = device_info.get("serial_number", entry.entry_id)
        
        self._attr_unique_id = f"{serial}_{info_key}"
        self._attr_name = name
        self._attr_icon = icon
        if entity_category:
            self._attr_entity_category = entity_category

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
    def native_value(self) -> str | None:
        """Return the state of the sensor."""
        device_data = self.coordinator.data.get("device_info", {})
        return device_data.get(self._info_key)


class APCPDURatedVoltageSensor(CoordinatorEntity[APCPDUDataUpdateCoordinator], SensorEntity):
    """Sensor for rated voltage."""

    _attr_has_entity_name = True
    _attr_device_class = SensorDeviceClass.VOLTAGE
    _attr_native_unit_of_measurement = UnitOfElectricPotential.VOLT
    _attr_icon = "mdi:lightning-bolt"

    def __init__(
        self,
        coordinator: APCPDUDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._entry = entry
        
        device_info = coordinator.data.get("device_info", {})
        serial = device_info.get("serial_number", entry.entry_id)
        
        self._attr_unique_id = f"{serial}_rated_voltage"
        self._attr_name = "Rated Voltage"

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
    def native_value(self) -> int | None:
        """Return the state of the sensor."""
        pdu_status = self.coordinator.data.get("pdu_status", {})
        return pdu_status.get("rated_voltage")


class APCPDURatedCurrentSensor(CoordinatorEntity[APCPDUDataUpdateCoordinator], SensorEntity):
    """Sensor for rated max current."""

    _attr_has_entity_name = True
    _attr_device_class = SensorDeviceClass.CURRENT
    _attr_native_unit_of_measurement = UnitOfElectricCurrent.AMPERE
    _attr_icon = "mdi:current-ac"

    def __init__(
        self,
        coordinator: APCPDUDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._entry = entry
        
        device_info = coordinator.data.get("device_info", {})
        serial = device_info.get("serial_number", entry.entry_id)
        
        self._attr_unique_id = f"{serial}_rated_max_current"
        self._attr_name = "Rated Max Current"

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
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        pdu_status = self.coordinator.data.get("pdu_status", {})
        return pdu_status.get("rated_max_current")


class APCPDUBankLoadSensor(CoordinatorEntity[APCPDUDataUpdateCoordinator], SensorEntity):
    """Sensor for bank load state."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:gauge"

    def __init__(
        self,
        coordinator: APCPDUDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._entry = entry
        
        device_info = coordinator.data.get("device_info", {})
        serial = device_info.get("serial_number", entry.entry_id)
        
        self._attr_unique_id = f"{serial}_bank_load_state"
        self._attr_name = "Bank Load State"

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
    def native_value(self) -> str | None:
        """Return the state of the sensor."""
        pdu_status = self.coordinator.data.get("pdu_status", {})
        return pdu_status.get("bank_load_state")


class APCPDUOutletPowerSensor(CoordinatorEntity[APCPDUDataUpdateCoordinator], SensorEntity):
    """Sensor for outlet power consumption."""

    _attr_has_entity_name = True
    _attr_device_class = SensorDeviceClass.POWER
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: APCPDUDataUpdateCoordinator,
        entry: ConfigEntry,
        outlet_num: int,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._entry = entry
        self.outlet_num = outlet_num
        
        device_info = coordinator.data.get("device_info", {})
        serial = device_info.get("serial_number", entry.entry_id)
        
        self._attr_unique_id = f"{serial}_outlet_{outlet_num}_power"
        self._attr_name = f"Outlet {outlet_num} Power"

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
    def native_value(self) -> int | None:
        """Return the state of the sensor."""
        outlet_data = self.coordinator.data.get("outlets", {}).get(self.outlet_num, {})
        return outlet_data.get("power")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        outlet_data = self.coordinator.data.get("outlets", {}).get(self.outlet_num, {})
        
        return {
            "outlet_number": self.outlet_num,
            "outlet_name": outlet_data.get("name"),
            "outlet_status": outlet_data.get("status"),
        }

