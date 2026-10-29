"""Shared fixtures for the APC PDU tests."""

from __future__ import annotations

import sys
from collections.abc import Generator
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from custom_components.apc_pdu_manager.snmp import (  # noqa: E402
    APCPDUError,
    LoadEntry,
    OutletStatus,
    PDUInfo,
    PDUStatus,
    SNMPAuth,
)

SERIAL = "ZA0123456789"
HOST = "192.0.2.10"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> None:
    """Load custom_components/ in every test."""


class FakePDU:
    """In-memory stand-in for APCPDUClient, shared by every client instance."""

    def __init__(self) -> None:
        self.info = PDUInfo(
            model="AP7920",
            serial=SERIAL,
            name="Rack A",
            firmware="v3.7.3",
            hardware="HW05",
            outlet_count=8,
            rated_current=10,
            nominal_voltage=230,
            has_power=True,
            has_outlet_current=False,
            loads=[LoadEntry(index=1, phase=1, bank=0)],
        )
        self.outlets = {n: n % 2 == 1 for n in range(1, 9)}
        self.names = {n: f"Outlet {n}" for n in range(1, 9)}
        self.names[1] = "Router"
        self.load_current = {1: 1.7}
        self.load_state = {1: "normal"}
        self.power = 380
        self.info_error: Exception | None = None
        self.status_error: Exception | None = None
        self.set_error: Exception | None = None
        self.set_calls: list[tuple[int, bool]] = []
        self.created: list[dict[str, Any]] = []
        self.closed = 0

    def status(self) -> PDUStatus:
        return PDUStatus(
            outlets={
                n: OutletStatus(
                    name=self.names[n],
                    is_on=on,
                    current=(n / 10 if self.info.has_outlet_current else None),
                )
                for n, on in self.outlets.items()
            },
            load_current=dict(self.load_current),
            load_state=dict(self.load_state),
            power=self.power if self.info.has_power else None,
        )


class FakeClient:
    """Mimics the public API of APCPDUClient."""

    def __init__(self, pdu: FakePDU, host: str, auth: SNMPAuth, port: int = 161) -> None:
        self._pdu = pdu
        self.host = host
        self.port = port
        pdu.created.append({"host": host, "auth": auth, "port": port})

    async def async_get_info(self) -> PDUInfo:
        if self._pdu.info_error:
            raise self._pdu.info_error
        return self._pdu.info

    async def async_get_status(self, info: PDUInfo) -> PDUStatus:
        if self._pdu.status_error:
            raise self._pdu.status_error
        return self._pdu.status()

    async def async_set_outlet(self, outlet: int, on: bool) -> None:
        if self._pdu.set_error:
            raise self._pdu.set_error
        self._pdu.set_calls.append((outlet, on))
        self._pdu.outlets[outlet] = on

    async def async_close(self) -> None:
        self._pdu.closed += 1


@pytest.fixture
def pdu() -> Generator[FakePDU]:
    """Patch the SNMP client with an in-memory PDU."""
    fake = FakePDU()

    def factory(host: str, auth: SNMPAuth, port: int = 161, **_: Any) -> FakeClient:
        return FakeClient(fake, host, auth, port)

    with patch("custom_components.apc_pdu_manager.coordinator.APCPDUClient", side_effect=factory):
        yield fake


__all__ = ["APCPDUError", "HOST", "SERIAL", "FakePDU"]
