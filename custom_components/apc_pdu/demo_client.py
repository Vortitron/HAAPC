"""Demo/Mock SNMP client for testing APC PDU without hardware."""
from __future__ import annotations

import logging
import random
from typing import Any

_LOGGER = logging.getLogger(__name__)


class DemoSNMPClient:
    """Demo SNMP client that simulates an APC PDU for testing.
    
    Can optionally try real SNMP first and fall back to simulated data.
    """

    def __init__(
        self, 
        host: str, 
        community: str, 
        version: str = "1",
        try_real_snmp: bool = True
    ) -> None:
        """Initialize the demo SNMP client.
        
        Args:
            host: PDU IP address
            community: SNMP community string
            version: SNMP version (1 or 2c)
            try_real_snmp: If True, try to use real SNMP first before falling back to demo
        """
        self.host = host
        self.community = community
        self.version = version
        self.try_real_snmp = try_real_snmp
        self._real_client = None
        
        # Try to initialize real SNMP client if requested
        if try_real_snmp:
            _LOGGER.warning("Demo Mode: Attempting to use real SNMP first...")
            try:
                # Try importing and initializing real SNMP client
                from .snmp_client import SNMPClient, SNMP_AVAILABLE
                
                if SNMP_AVAILABLE:
                    self._real_client = SNMPClient(host, community, version)
                    _LOGGER.warning("✅ Demo Mode: Real SNMP client available, will try real PDU first")
                else:
                    _LOGGER.warning("⚠️ Demo Mode: pysnmp not available, using pure simulation")
            except Exception as ex:
                _LOGGER.warning("⚠️ Demo Mode: Cannot use real SNMP (%s), using pure simulation", ex)
        else:
            _LOGGER.warning("Demo Mode: Pure simulation (not trying real SNMP)")
        
        # Simulated outlet states (all start as off)
        self._outlet_states = {i: False for i in range(1, 9)}
        
        # Simulated device info
        self._device_info = {
            "name": "Demo PDU",
            "model": "AP7920 (Demo)",
            "serial_number": f"DEMO-{host.replace('.', '-')}",
            "firmware": "v3.7.4 (Demo)",
            "hardware": "v05 (Demo)",
            "outlet_count": 8,
        }
        
        _LOGGER.warning("Demo SNMP client initialized for %s (real_snmp=%s)", host, try_real_snmp)

    def _snmp_get(self, oid: str) -> Any:
        """Simulate SNMP get - not used in demo mode."""
        return None

    def _snmp_set(self, oid: str, value: int) -> bool:
        """Simulate SNMP set - not used in demo mode."""
        return True

    def get_device_info(self) -> dict[str, Any]:
        """Get device information - try real SNMP first, fallback to simulated."""
        if self._real_client:
            try:
                _LOGGER.warning("Demo Mode: Trying real SNMP for device info...")
                real_info = self._real_client.get_device_info()
                if real_info and real_info.get("model"):
                    _LOGGER.warning("✅ Demo Mode: Got real device info: %s", real_info)
                    # Add "(Demo Mode)" suffix to model to indicate we're in demo
                    real_info["model"] = f"{real_info['model']} (Demo Mode)"
                    return real_info
                else:
                    _LOGGER.warning("⚠️ Demo Mode: Real SNMP returned no data, using simulation")
            except Exception as ex:
                _LOGGER.warning("⚠️ Demo Mode: Real SNMP failed (%s), using simulation", ex)
        
        _LOGGER.info("Demo Mode: Using simulated device info")
        return self._device_info.copy()

    def get_pdu_status(self) -> dict[str, Any]:
        """Get simulated PDU status."""
        # Calculate simulated total power based on outlets that are on
        on_count = sum(1 for state in self._outlet_states.values() if state)
        
        return {
            "rated_voltage": 120,
            "rated_max_current": 20.0,
            "bank_load_state": "Normal" if on_count < 6 else "Near Overload" if on_count < 8 else "High Load",
        }

    def get_outlet_count(self) -> int:
        """Get number of outlets."""
        return 8

    def get_outlet_status(self, outlet_num: int) -> dict[str, Any]:
        """Get outlet status - try real SNMP first, fallback to simulated."""
        if self._real_client:
            try:
                real_status = self._real_client.get_outlet_status(outlet_num)
                if real_status and real_status.get("name"):
                    _LOGGER.debug("Demo Mode: Got real outlet %d status", outlet_num)
                    return real_status
            except Exception as ex:
                _LOGGER.debug("Demo Mode: Real SNMP failed for outlet %d (%s), using simulation", outlet_num, ex)
        
        # Use simulated data
        is_on = self._outlet_states.get(outlet_num, False)
        
        # Simulate different power levels for different outlets
        base_power = {
            1: 145,  # Server 1
            2: 180,  # Server 2
            3: 45,   # Network switch
            4: 25,   # Router
            5: 90,   # NAS
            6: 120,  # Workstation
            7: 60,   # Monitor
            8: 35,   # Misc
        }.get(outlet_num, 50)
        
        # Add some random variation (+/- 10%)
        power = int(base_power * (0.9 + random.random() * 0.2)) if is_on else 0
        
        # Outlet names
        names = {
            1: "Server 1",
            2: "Server 2", 
            3: "Network Switch",
            4: "Router",
            5: "NAS",
            6: "Workstation",
            7: "Monitor",
            8: "Misc Device",
        }
        
        return {
            "name": names.get(outlet_num, f"Outlet {outlet_num}"),
            "status": "On" if is_on else "Off",
            "power": power,
            "is_on": is_on,
        }

    def get_all_outlets_status(self) -> dict[int, dict[str, Any]]:
        """Get simulated status for all outlets."""
        outlets = {}
        for i in range(1, 9):
            outlets[i] = self.get_outlet_status(i)
        return outlets

    def set_outlet(self, outlet_num: int, state: bool) -> bool:
        """Set outlet state - try real SNMP first, fallback to simulated."""
        if self._real_client:
            try:
                _LOGGER.warning("Demo Mode: Trying real SNMP to set outlet %d to %s", outlet_num, "ON" if state else "OFF")
                result = self._real_client.set_outlet(outlet_num, state)
                if result:
                    _LOGGER.warning("✅ Demo Mode: Successfully set outlet %d on real PDU", outlet_num)
                    # Also update our simulated state
                    self._outlet_states[outlet_num] = state
                    return True
                else:
                    _LOGGER.warning("⚠️ Demo Mode: Real SNMP set failed, using simulation")
            except Exception as ex:
                _LOGGER.warning("⚠️ Demo Mode: Real SNMP set failed (%s), using simulation", ex)
        
        # Simulate the operation
        _LOGGER.info("Demo: Simulating outlet %d set to %s", outlet_num, "ON" if state else "OFF")
        
        if 1 <= outlet_num <= 8:
            self._outlet_states[outlet_num] = state
            return True
        return False

    def set_all_outlets(self, state: bool) -> bool:
        """Simulate turning all outlets on or off."""
        _LOGGER.info("Demo: Setting all outlets to %s", "ON" if state else "OFF")
        
        for i in range(1, 9):
            self._outlet_states[i] = state
        return True

