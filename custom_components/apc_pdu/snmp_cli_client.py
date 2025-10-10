"""SNMP client using command-line tools (fallback for broken pysnmp)."""
from __future__ import annotations

import logging
import subprocess
from typing import Any

_LOGGER = logging.getLogger(__name__)


class SNMPCLIClient:
    """SNMP client using command-line snmpget/snmpset tools.
    
    This is a fallback for when pysnmp has dependency issues.
    Requires snmp package to be installed on the system.
    """

    def __init__(self, host: str, community: str, version: str = "1") -> None:
        """Initialize the CLI SNMP client."""
        self.host = host
        self.community = community
        self.version = version
        
        # Check if snmpget is available
        try:
            subprocess.run(
                ["snmpget", "--version"],
                capture_output=True,
                timeout=2,
                check=False
            )
            _LOGGER.debug("snmpget command found and available")
        except (FileNotFoundError, subprocess.TimeoutExpired):
            import os
            if os.path.exists('/usr/src/homeassistant'):
                _LOGGER.error(
                    "⚠️ Home Assistant OS detected. Command-line SNMP tools not available. "
                    "CLI fallback won't work. Please use Demo Mode for testing. "
                    "See HAOS_COMPATIBILITY.md for details."
                )
                # Raise an error so config flow knows CLI isn't available
                raise ImportError(
                    "SNMP CLI tools not available in Home Assistant OS. "
                    "Use Demo Mode or wait for pysnmp to be fixed in HA Core."
                )
            else:
                _LOGGER.warning(
                    "snmpget command not found. For Home Assistant Core, install with: "
                    "sudo apt-get install snmp (Debian/Ubuntu) or "
                    "sudo yum install net-snmp-utils (RedHat/CentOS)"
                )
                # Raise an error so config flow knows CLI isn't available
                raise ImportError(
                    "SNMP CLI tools (snmpget/snmpset) not installed. "
                    "Install with: sudo apt-get install snmp"
                )

    def _snmp_get(self, oid: str) -> Any:
        """Get a single SNMP value using command-line tool."""
        try:
            # Use snmpget command
            cmd = [
                "snmpget",
                f"-v{self.version}",
                "-c", self.community,
                "-Oqv",  # Output: quick print, value only
                "-t", "5",  # Timeout 5 seconds
                "-r", "2",  # 2 retries
                self.host,
                oid
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10,
                check=False
            )
            
            if result.returncode != 0:
                _LOGGER.debug(
                    "snmpget failed for OID %s: %s",
                    oid,
                    result.stderr
                )
                return None
            
            # Parse output
            value = result.stdout.strip()
            
            # Remove quotes if present
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            
            # Try to convert to int if it's numeric
            if value.isdigit():
                return int(value)
            
            return value
            
        except (subprocess.TimeoutExpired, FileNotFoundError) as ex:
            _LOGGER.debug("snmpget exception for OID %s: %s", oid, ex)
            return None

    def _snmp_set(self, oid: str, value: int) -> bool:
        """Set a single SNMP value using command-line tool."""
        try:
            # Use snmpset command
            cmd = [
                "snmpset",
                f"-v{self.version}",
                "-c", self.community,
                "-t", "5",
                "-r", "2",
                self.host,
                oid,
                "i",  # Integer type
                str(value)
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10,
                check=False
            )
            
            if result.returncode != 0:
                _LOGGER.error(
                    "snmpset failed for OID %s: %s",
                    oid,
                    result.stderr
                )
                return False
            
            return True
            
        except (subprocess.TimeoutExpired, FileNotFoundError) as ex:
            _LOGGER.error("snmpset exception for OID %s: %s", oid, ex)
            return False

    # Import all the same methods from SNMPClient
    def get_device_info(self) -> dict[str, Any]:
        """Get device information."""
        from .const import (
            OID_FIRMWARE_REV,
            OID_HARDWARE_REV,
            OID_MODEL,
            OID_OUTLET_COUNT,
            OID_PDU_NAME,
            OID_SERIAL,
        )
        
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
        from .const import (
            BANK_LOAD_STATE,
            OID_BANK_LOAD_STATE,
            OID_RATED_MAX_CURRENT,
            OID_RATED_VOLTAGE,
        )
        
        rated_current = self._snmp_get(OID_RATED_MAX_CURRENT)
        
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
        from .const import OID_OUTLET_COUNT
        
        count = self._snmp_get(OID_OUTLET_COUNT)
        try:
            return int(count) if count else 8
        except (ValueError, TypeError):
            return 8

    def get_outlet_status(self, outlet_num: int) -> dict[str, Any]:
        """Get status for a specific outlet."""
        from .const import (
            OID_OUTLET_NAME,
            OID_OUTLET_POWER,
            OID_OUTLET_STATUS,
            OUTLET_STATUS,
        )
        
        name = self._snmp_get(f"{OID_OUTLET_NAME}.{outlet_num}")
        status_raw = self._snmp_get(f"{OID_OUTLET_STATUS}.{outlet_num}")
        power = self._snmp_get(f"{OID_OUTLET_POWER}.{outlet_num}")
        
        status = None
        if status_raw is not None:
            try:
                status = OUTLET_STATUS.get(int(status_raw), "Unknown")
            except (ValueError, TypeError):
                status = "Unknown"
        
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
        from .const import (
            OID_OUTLET_CONTROL,
            SNMP_OUTLET_OFF,
            SNMP_OUTLET_ON,
        )
        
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

