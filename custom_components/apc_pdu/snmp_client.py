"""SNMP client for APC PDU."""
from __future__ import annotations

import logging
from typing import Any

# Use the EXACT same pysnmp import path as Home Assistant's SNMP integration
# HA uses pysnmp.hlapi.v3arch.asyncio - we'll use it too and run in executor
_IMPORT_ERROR = ""
_IS_ASYNC = False
try:
    # Try the exact path HA uses (asyncio version)
    from pysnmp.hlapi.v3arch.asyncio import (
        CommunityData,
        ContextData,
        ObjectIdentity,
        ObjectType,
        SnmpEngine,
        UdpTransportTarget,
        get_cmd,
        set_cmd,
    )
    SNMP_AVAILABLE = True
    _IMPORT_SOURCE = "pysnmp.hlapi.v3arch.asyncio"
    _IS_ASYNC = True
except ImportError as err:
    # Try sync version
    try:
        from pysnmp.hlapi.v3arch.sync import (
            CommunityData,
            ContextData,
            ObjectIdentity,
            ObjectType,
            SnmpEngine,
            UdpTransportTarget,
            getCmd,
            setCmd,
        )
        SNMP_AVAILABLE = True
        _IMPORT_SOURCE = "pysnmp.hlapi.v3arch.sync"
        _IS_ASYNC = False
    except ImportError as err2:
        # Try the old import path as last resort
        try:
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
            SNMP_AVAILABLE = True
            _IMPORT_SOURCE = "pysnmp.hlapi"
            _IS_ASYNC = False
        except ImportError as err3:
            # pysnmp not available or broken dependencies
            SNMP_AVAILABLE = False
            _IMPORT_SOURCE = "none"
            _IS_ASYNC = False
            _IMPORT_ERROR = f"v3arch.asyncio: {err}, v3arch.sync: {err2}, hlapi: {err3}"

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

# Log which import source we're using
if SNMP_AVAILABLE:
    _LOGGER.info("✅ Successfully imported pysnmp from: %s (async=%s)", _IMPORT_SOURCE, _IS_ASYNC)
else:
    _LOGGER.error("❌ Failed to import pysnmp: %s", _IMPORT_ERROR)


class SNMPClient:
    """SNMP client for APC PDU."""

    def __init__(self, host: str, community: str, version: str = "1") -> None:
        """Initialize the SNMP client."""
        if not SNMP_AVAILABLE:
            _LOGGER.error("pysnmp import failed: %s", _IMPORT_ERROR)
            raise ImportError(
                f"pysnmp is not available or has broken dependencies. "
                f"Error: {_IMPORT_ERROR}. "
                f"Please use Demo Mode or CLI fallback"
            )
        
        self.host = host
        self.community = community
        self.version = 0 if version == "1" else 1  # 0 = v1, 1 = v2c
        self.port = 161
        
        _LOGGER.warning(
            "SNMPClient initialized: host=%s, version=%s (mpModel=%d), port=%d",
            host, version, self.version, self.port
        )

    def _snmp_get(self, oid: str) -> Any:
        """Get a single SNMP value."""
        try:
            _LOGGER.info("SNMP GET: %s from %s (community: %s***, version: %s)", 
                        oid, self.host, self.community[:2], self.version)
            
            if _IS_ASYNC:
                # Use async version
                import asyncio
                return asyncio.run(self._snmp_get_async(oid))
            
            # Use sync version
            iterator = getCmd(
                SnmpEngine(),
                CommunityData(self.community, mpModel=self.version),
                UdpTransportTarget((self.host, self.port), timeout=5, retries=2),
                ContextData(),
                ObjectType(ObjectIdentity(oid)),
            )
            
            error_indication, error_status, error_index, var_binds = next(iterator)
            
            if error_indication:
                _LOGGER.error("SNMP error indication for OID %s: %s", oid, error_indication)
                return None
            elif error_status:
                _LOGGER.error(
                    "SNMP error status for OID %s: %s at %s",
                    oid,
                    error_status.prettyPrint(),
                    error_index and var_binds[int(error_index) - 1][0] or "?",
                )
                return None
            else:
                for var_bind in var_binds:
                    value = var_bind[1]
                    # Convert to string if it's a DisplayString or similar
                    if hasattr(value, 'prettyPrint'):
                        result = value.prettyPrint()
                    # Convert to int if it's a numeric string
                    elif isinstance(value, str) and value.isdigit():
                        result = int(value)
                    else:
                        result = value
                    _LOGGER.info("SNMP GET result for %s: %s (type: %s)", oid, result, type(result).__name__)
                    return result
                    
        except Exception as ex:
            _LOGGER.error("SNMP get exception for OID %s: %s (type: %s)", oid, ex, type(ex).__name__, exc_info=True)
            return None

    async def _snmp_get_async(self, oid: str) -> Any:
        """Get a single SNMP value using async API."""
        try:
            # Async API requires calling .create() to construct target
            target = await UdpTransportTarget.create((self.host, self.port))
            target.timeout = 5
            target.retries = 2
            
            error_indication, error_status, error_index, var_binds = await get_cmd(
                SnmpEngine(),
                CommunityData(self.community, mpModel=self.version),
                target,
                ContextData(),
                ObjectType(ObjectIdentity(oid)),
            )
            
            if error_indication:
                _LOGGER.error("SNMP error indication for OID %s: %s", oid, error_indication)
                return None
            elif error_status:
                _LOGGER.error(
                    "SNMP error status for OID %s: %s at %s",
                    oid,
                    error_status.prettyPrint(),
                    error_index and var_binds[int(error_index) - 1][0] or "?",
                )
                return None
            else:
                for var_bind in var_binds:
                    value = var_bind[1]
                    # Convert to string if it's a DisplayString or similar
                    if hasattr(value, 'prettyPrint'):
                        result = value.prettyPrint()
                    # Convert to int if it's a numeric string
                    elif isinstance(value, str) and value.isdigit():
                        result = int(value)
                    else:
                        result = value
                    _LOGGER.info("SNMP GET (async) result for %s: %s (type: %s)", oid, result, type(result).__name__)
                    return result
        except Exception as ex:
            _LOGGER.error("SNMP get (async) exception for OID %s: %s", oid, ex, exc_info=True)
            return None

    def _snmp_set(self, oid: str, value: int) -> bool:
        """Set a single SNMP value."""
        try:
            if _IS_ASYNC:
                # Use async version
                import asyncio
                return asyncio.run(self._snmp_set_async(oid, value))
            
            # Use sync version
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

    async def _snmp_set_async(self, oid: str, value: int) -> bool:
        """Set a single SNMP value using async API."""
        try:
            from pysnmp.proto.rfc1902 import Integer
            
            # Async API requires calling .create() to construct target
            target = await UdpTransportTarget.create((self.host, self.port))
            target.timeout = 5
            target.retries = 2
            
            error_indication, error_status, error_index, var_binds = await set_cmd(
                SnmpEngine(),
                CommunityData(self.community, mpModel=self.version),
                target,
                ContextData(),
                ObjectType(ObjectIdentity(oid), Integer(value)),
            )
            
            if error_indication or error_status:
                _LOGGER.error(
                    "SNMP set (async) failed: %s %s", error_indication, error_status
                )
                return False
            return True
        except Exception as ex:
            _LOGGER.error("SNMP set (async) exception for OID %s: %s", oid, ex, exc_info=True)
            return False

    def get_device_info(self) -> dict[str, Any]:
        """Get device information."""
        _LOGGER.warning("Getting device info from %s...", self.host)
        result = {
            "name": self._snmp_get(OID_PDU_NAME),
            "model": self._snmp_get(OID_MODEL),
            "serial_number": self._snmp_get(OID_SERIAL),
            "firmware": self._snmp_get(OID_FIRMWARE_REV),
            "hardware": self._snmp_get(OID_HARDWARE_REV),
            "outlet_count": self._snmp_get(OID_OUTLET_COUNT),
        }
        _LOGGER.warning("Device info result: %s", result)
        return result

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

