"""SNMP client for APC PDU."""
from __future__ import annotations

import logging
from typing import Any

from pysnmp.hlapi import (
    CommunityData,
    ContextData,
    ObjectIdentity,
    ObjectType,
    SnmpEngine,
    UdpTransportTarget,
    getCmd,
    setCmd,
)

from .const import (
    BANK_LOAD_STATE,
    OID_BANK_LOAD_STATE,
    OID_FIRMWARE_REV,
    OID_HARDWARE_REV,
    OID_MODEL,
    OID_OUTLET_CONTROL,
    OID_OUTLET_COUNT,
    OID_OUTLET_NAME,
    OID_OUTLET_POWER,
    OID_OUTLET_STATUS,
    OID_PDU_NAME,
    OID_RATED_MAX_CURRENT,
    OID_RATED_VOLTAGE,
    OID_SERIAL,
    OUTLET_STATUS,
    SNMP_OUTLET_OFF,
    SNMP_OUTLET_ON,
)

_LOGGER = logging.getLogger(__name__)


class SNMPClient:
    """SNMP client for APC PDU."""

    def __init__(self, host: str, community: str, version: str = "1") -> None:
        """Initialize the SNMP client."""
        self.host = host
        self.community = community
        self.version = 0 if version == "1" else 1  # 0 = v1, 1 = v2c
        self.port = 161

    def _snmp_get(self, oid: str) -> Any:
        """Get a single SNMP value."""
        try:
            iterator = getCmd(
                SnmpEngine(),
                CommunityData(self.community, mpModel=self.version),
                UdpTransportTarget((self.host, self.port), timeout=5, retries=2),
                ContextData(),
                ObjectType(ObjectIdentity(oid)),
            )
            
            error_indication, error_status, error_index, var_binds = next(iterator)
            
            if error_indication:
                _LOGGER.debug("SNMP error indication: %s", error_indication)
                return None
            elif error_status:
                _LOGGER.debug(
                    "SNMP error status: %s at %s",
                    error_status.prettyPrint(),
                    error_index and var_binds[int(error_index) - 1][0] or "?",
                )
                return None
            else:
                for var_bind in var_binds:
                    value = var_bind[1]
                    # Convert to string if it's a DisplayString or similar
                    if hasattr(value, 'prettyPrint'):
                        return value.prettyPrint()
                    return int(value) if value.isdigit() if isinstance(value, str) else value
                    
        except Exception as ex:
            _LOGGER.debug("SNMP get exception for OID %s: %s", oid, ex)
            return None

    def _snmp_set(self, oid: str, value: int) -> bool:
        """Set a single SNMP value."""
        try:
            from pysnmp.hlapi import Integer

            iterator = setCmd(
                SnmpEngine(),
                CommunityData(self.community, mpModel=self.version),
                UdpTransportTarget((self.host, self.port), timeout=5, retries=2),
                ContextData(),
                ObjectType(ObjectIdentity(oid), Integer(value)),
            )
            
            error_indication, error_status, error_index, var_binds = next(iterator)
            
            if error_indication or error_status:
                _LOGGER.error(
                    "SNMP set failed: %s %s", error_indication, error_status
                )
                return False
            return True
            
        except Exception as ex:
            _LOGGER.error("SNMP set exception for OID %s: %s", oid, ex)
            return False

    def get_device_info(self) -> dict[str, Any]:
        """Get device information."""
        return {
            "name": self._snmp_get(OID_PDU_NAME),
            "model": self._snmp_get(OID_MODEL),
            "serial_number": self._snmp_get(OID_SERIAL),
            "firmware": self._snmp_get(OID_FIRMWARE_REV),
            "hardware": self._snmp_get(OID_HARDWARE_REV),
            "outlet_count": self._snmp_get(OID_OUTLET_COUNT),
        }

    def get_pdu_status(self) -> dict[str, Any]:
        """Get overall PDU status."""
        rated_current = self._snmp_get(OID_RATED_MAX_CURRENT)
        
        # Convert current from tenths to amps
        if rated_current is not None:
            try:
                rated_current = float(rated_current) / 100
            except (ValueError, TypeError):
                rated_current = None
        
        bank_load_state = self._snmp_get(OID_BANK_LOAD_STATE)
        bank_load_state_str = None
        if bank_load_state is not None:
            try:
                bank_load_state_str = BANK_LOAD_STATE.get(int(bank_load_state))
            except (ValueError, TypeError):
                pass
        
        return {
            "rated_voltage": self._snmp_get(OID_RATED_VOLTAGE),
            "rated_max_current": rated_current,
            "bank_load_state": bank_load_state_str,
        }

    def get_outlet_count(self) -> int:
        """Get number of outlets."""
        count = self._snmp_get(OID_OUTLET_COUNT)
        try:
            return int(count) if count else 8
        except (ValueError, TypeError):
            return 8

    def get_outlet_status(self, outlet_num: int) -> dict[str, Any]:
        """Get status for a specific outlet."""
        name = self._snmp_get(f"{OID_OUTLET_NAME}.{outlet_num}")
        status_raw = self._snmp_get(f"{OID_OUTLET_STATUS}.{outlet_num}")
        power = self._snmp_get(f"{OID_OUTLET_POWER}.{outlet_num}")
        
        status = None
        if status_raw is not None:
            try:
                status = OUTLET_STATUS.get(int(status_raw), "Unknown")
            except (ValueError, TypeError):
                status = "Unknown"
        
        # Convert power to int if possible
        if power is not None:
            try:
                power = int(power)
            except (ValueError, TypeError):
                power = None
        
        return {
            "name": name or f"Outlet {outlet_num}",
            "status": status,
            "power": power,
            "is_on": status == "On" if status else None,
        }

    def get_all_outlets_status(self) -> dict[int, dict[str, Any]]:
        """Get status for all outlets."""
        outlet_count = self.get_outlet_count()
        outlets = {}
        
        for i in range(1, outlet_count + 1):
            outlets[i] = self.get_outlet_status(i)
        
        return outlets

    def set_outlet(self, outlet_num: int, state: bool) -> bool:
        """Turn outlet on or off."""
        value = SNMP_OUTLET_ON if state else SNMP_OUTLET_OFF
        return self._snmp_set(f"{OID_OUTLET_CONTROL}.{outlet_num}", value)

    def set_all_outlets(self, state: bool) -> bool:
        """Turn all outlets on or off."""
        outlet_count = self.get_outlet_count()
        success = True
        
        for i in range(1, outlet_count + 1):
            if not self.set_outlet(i, state):
                success = False
        
        return success

