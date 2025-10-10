"""Demo/Mock SNMP client for testing APC PDU without hardware."""
from __future__ import annotations

import logging
import random
from typing import Any

_LOGGER = logging.getLogger(__name__)


class DemoSNMPClient:
    """Demo SNMP client that simulates an APC PDU for testing."""

    def __init__(self, host: str, community: str, version: str = "1") -> None:
        """Initialize the demo SNMP client."""
        self.host = host
        self.community = community
        self.version = version
        
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
        
        _LOGGER.info("Demo SNMP client initialized for %s", host)

    def _snmp_get(self, oid: str) -> Any:
        """Simulate SNMP get - not used in demo mode."""
        return None

    def _snmp_set(self, oid: str, value: int) -> bool:
        """Simulate SNMP set - not used in demo mode."""
        return True

    def get_device_info(self) -> dict[str, Any]:
        """Get simulated device information."""
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
        """Get simulated status for a specific outlet."""
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
        """Simulate turning outlet on or off."""
        _LOGGER.info("Demo: Setting outlet %d to %s", outlet_num, "ON" if state else "OFF")
        
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

