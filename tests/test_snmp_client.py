"""Run the real pysnmp client against a fake APC agent on 127.0.0.1."""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
from homeassistant import block_async_io

from custom_components.apc_pdu_manager.const import (
    SNMP_VERSION_1,
    SNMP_VERSION_2C,
    SNMP_VERSION_3,
)
from custom_components.apc_pdu_manager.snmp import (
    APCPDUClient,
    CannotConnect,
    CommandFailed,
    InvalidAuth,
    LoadEntry,
    NotSupported,
    SNMPAuth,
)

from .fake_agent import (
    RPDU,
    RPDU2,
    SPDU,
    FakeAPCAgent,
    ap7920_values,
    ap8941_values,
    ap9211_values,
    close_v3_agent,
    start_v3_agent,
)


@pytest.fixture
async def agent(socket_enabled: None, disable_block_async_io: None) -> AsyncIterator[FakeAPCAgent]:
    """Start a fake AP7920 on a free UDP port.

    Home Assistant's event-loop protection is switched on, as in production,
    so any blocking I/O done by pysnmp inside the loop fails the test.
    """
    block_async_io.enable()
    fake = FakeAPCAgent(ap7920_values())
    await fake.start()
    yield fake
    fake.stop()


async def _client(agent: FakeAPCAgent, auth: SNMPAuth) -> APCPDUClient:
    return APCPDUClient("127.0.0.1", auth, port=agent.port, timeout=0.5, retries=0)


@pytest.mark.parametrize("version", [SNMP_VERSION_1, SNMP_VERSION_2C])
async def test_read_ap7920(agent: FakeAPCAgent, version: str) -> None:
    """Identity, optional OIDs and outlet states decode correctly."""
    client = await _client(agent, SNMPAuth(version=version, community="public"))
    try:
        info = await client.async_get_info()
        assert info.model == "AP7920"
        assert info.serial == "ZA0123456789"
        assert info.name == "RackPDU"
        assert info.firmware == "v3.7.3"
        assert info.outlet_count == 8
        assert info.rated_current == 10
        assert info.nominal_voltage == 230
        # Not implemented by this PDU, so no sensors must be created for them
        assert info.has_power is False
        assert info.has_outlet_current is False
        assert info.loads == [LoadEntry(index=1, phase=1, bank=0)]

        status = await client.async_get_status(info)
        assert status.outlets[1].is_on is True
        assert status.outlets[2].is_on is False
        assert status.outlets[3].name == "Outlet 3"
        assert status.load_current == {1: 1.7}
        assert status.load_state == {1: "normal"}
        assert status.power is None
    finally:
        await client.async_close()


async def test_optional_values_and_banks(agent: FakeAPCAgent) -> None:
    """A metered, banked PDU exposes power, bank and outlet currents."""
    agent.values.update(
        {
            f"{RPDU}.1.16.0": 412,
            f"{RPDU}.2.1.4.0": 2,
            f"{RPDU}.3.1.5.0": 8,
            f"{RPDU}.2.3.1.1.2.2": 9,
            f"{RPDU}.2.3.1.1.3.2": 3,
            f"{RPDU}.2.3.1.1.4.2": 0,
            f"{RPDU}.2.3.1.1.5.2": 1,
            f"{RPDU}.2.3.1.1.2.3": 8,
            f"{RPDU}.2.3.1.1.3.3": 2,
            f"{RPDU}.2.3.1.1.4.3": 0,
            f"{RPDU}.2.3.1.1.5.3": 2,
            **{f"{RPDU}.3.5.1.1.7.{n}": n for n in range(1, 9)},
        }
    )
    client = await _client(agent, SNMPAuth(version=SNMP_VERSION_1, community="public"))
    try:
        info = await client.async_get_info()
        assert info.has_power and info.has_outlet_current
        assert [load.bank for load in info.loads] == [0, 1, 2]
        status = await client.async_get_status(info)
        assert status.power == 412
        assert status.load_current == {1: 1.7, 2: 0.9, 3: 0.8}
        assert status.load_state == {1: "normal", 2: "near_overload", 3: "low"}
        assert status.outlets[5].current == 0.5
    finally:
        await client.async_close()


@pytest.mark.parametrize("version", [SNMP_VERSION_1, SNMP_VERSION_2C])
async def test_switch_outlet(agent: FakeAPCAgent, version: str) -> None:
    """A SET with the write community switches the outlet."""
    client = await _client(agent, SNMPAuth(version=version, community="private"))
    try:
        await client.async_set_outlet(2, True)
        assert agent.values[f"{RPDU}.3.3.1.1.4.2"] == 1
        await client.async_set_outlet(1, False)
        assert agent.values[f"{RPDU}.3.3.1.1.4.1"] == 2
        info = await client.async_get_info()
        status = await client.async_get_status(info)
        assert status.outlets[1].is_on is False
        assert status.outlets[2].is_on is True
    finally:
        await client.async_close()


@pytest.mark.parametrize("version", [SNMP_VERSION_1, SNMP_VERSION_2C])
async def test_read_only_community_cannot_switch(agent: FakeAPCAgent, version: str) -> None:
    """A rejected SET is reported, not silently ignored."""
    client = await _client(agent, SNMPAuth(version=version, community="public"))
    try:
        with pytest.raises(CommandFailed):
            await client.async_set_outlet(2, True)
        assert agent.values[f"{RPDU}.3.3.1.1.4.2"] == 2
    finally:
        await client.async_close()


async def test_wrong_community_times_out(agent: FakeAPCAgent) -> None:
    """The agent drops unknown communities, which reads as no answer."""
    client = await _client(agent, SNMPAuth(version=SNMP_VERSION_2C, community="wrong"))
    try:
        with pytest.raises(CannotConnect):
            await client.async_get_info()
        assert agent.requests == 0
    finally:
        await client.async_close()


async def test_not_an_apc_pdu(agent: FakeAPCAgent) -> None:
    """A device without any APC PDU MIB is rejected."""
    agent.values.clear()
    agent.values["1.3.6.1.2.1.1.1.0"] = "Some switch"
    client = await _client(agent, SNMPAuth(version=SNMP_VERSION_1, community="public"))
    try:
        with pytest.raises(NotSupported):
            await client.async_get_info()
    finally:
        await client.async_close()


@pytest.mark.parametrize("version", [SNMP_VERSION_1, SNMP_VERSION_2C])
async def test_read_rpdu2(agent: FakeAPCAgent, version: str) -> None:
    """An AP89xx-style PDU is read through rPDU2, its chained neighbour left out."""
    agent.values = ap8941_values()
    client = await _client(agent, SNMPAuth(version=version, community="public"))
    try:
        info = await client.async_get_info()
        assert info.mib == "rpdu2"
        assert (info.model, info.serial, info.name) == ("AP8941", "5A1234E56789", "Rack B")
        assert info.firmware == "v6.8.2"
        assert info.outlet_count == 8
        assert info.outlet_numbers == list(range(1, 9))
        assert info.metered_outlets == list(range(1, 9))
        assert info.rated_current == 16
        assert info.nominal_voltage is None
        assert info.has_power and info.has_energy and info.has_voltage
        assert info.loads == [
            LoadEntry(index=1, phase=1, row=1),
            LoadEntry(index=2, bank=1, row=1),
            LoadEntry(index=3, bank=2, row=2),
        ]

        status = await client.async_get_status(info)
        assert set(status.outlets) == set(range(1, 9))
        assert status.outlets[1].is_on is True  # rPDU2 reports on as 2
        assert status.outlets[2].is_on is False
        assert status.outlets[3].name == "PDU1 outlet 3"
        assert status.outlets[5].current == 0.5
        assert status.load_current == {1: 1.7, 2: 0.9, 3: 0.8}
        # rPDU2 numbers low (1) and normal (2) the other way round from rPDU
        assert status.load_state == {1: "normal", 2: "normal", 3: "near_overload"}
        assert status.voltage == {1: 231}
        assert status.power == 380
        assert status.energy == 1234.5
    finally:
        await client.async_close()


async def test_rpdu2_unsupported_values(agent: FakeAPCAgent) -> None:
    """-1 means the model does not measure it: no power, energy or voltage."""
    agent.values = ap8941_values()
    agent.values[f"{RPDU2}.4.3.1.5.1"] = -1
    agent.values[f"{RPDU2}.4.3.1.9.1"] = -1
    agent.values[f"{RPDU2}.6.3.1.6.1"] = -1
    agent.values[f"{RPDU2}.4.2.1.6.1"] = 0
    client = await _client(agent, SNMPAuth(version=SNMP_VERSION_2C, community="public"))
    try:
        info = await client.async_get_info()
        assert not (info.has_power or info.has_energy or info.has_voltage)
        assert info.metered_outlets == []
        status = await client.async_get_status(info)
        assert status.power is None and status.energy is None and status.voltage == {}
        assert status.outlets[4].current is None
    finally:
        await client.async_close()


async def test_switch_rpdu2_outlet(agent: FakeAPCAgent) -> None:
    """rPDU2 outlets are switched through the control table, by row."""
    agent.values = ap8941_values()
    client = await _client(agent, SNMPAuth(version=SNMP_VERSION_2C, community="private"))
    try:
        info = await client.async_get_info()
        await client.async_set_outlet(2, True)
        assert agent.values[f"{RPDU2}.9.2.4.1.5.2"] == 1
        await client.async_set_outlet(1, False)
        assert agent.values[f"{RPDU2}.9.2.4.1.5.1"] == 2
        status = await client.async_get_status(info)
        assert status.outlets[1].is_on is False
        assert status.outlets[2].is_on is True
        # The chained PDU's outlet 1 (row 9) was not touched
        assert agent.values[f"{RPDU2}.9.2.3.1.5.9"] == 2
    finally:
        await client.async_close()


@pytest.mark.parametrize("version", [SNMP_VERSION_1, SNMP_VERSION_2C])
async def test_read_and_switch_spdu(agent: FakeAPCAgent, version: str) -> None:
    """A MasterSwitch is driven through sPDU: outlets, no load readings."""
    agent.values = ap9211_values()
    client = await _client(agent, SNMPAuth(version=version, community="private"))
    try:
        info = await client.async_get_info()
        assert info.mib == "spdu"
        assert (info.model, info.serial, info.firmware) == ("AP9211", "WA9912345678", "v2.2.0")
        assert info.outlet_count == 8
        assert info.loads == []
        assert not (info.has_power or info.has_outlet_current or info.rated_current)
        status = await client.async_get_status(info)
        assert status.outlets[1].is_on is True
        assert status.outlets[2].is_on is False
        assert status.outlets[2].name == "Socket 2"
        await client.async_set_outlet(2, True)
        assert agent.values[f"{SPDU}.4.2.1.3.2"] == 1
        status = await client.async_get_status(info)
        assert status.outlets[2].is_on is True
    finally:
        await client.async_close()


async def test_rpdu_wins_over_spdu(agent: FakeAPCAgent) -> None:
    """An AP79xx answering both branches keeps the rPDU readings."""
    agent.values.update(ap9211_values())
    client = await _client(agent, SNMPAuth(version=SNMP_VERSION_1, community="public"))
    try:
        info = await client.async_get_info()
        assert info.mib == "rpdu"
        assert info.model == "AP7920"
        assert info.loads
    finally:
        await client.async_close()


async def test_snmpv3_user_unknown(agent: FakeAPCAgent) -> None:
    """The fake agent speaks no SNMPv3, so an SNMPv3 request gets no answer."""
    client = await _client(
        agent,
        SNMPAuth(
            version=SNMP_VERSION_3,
            username="ha",
            auth_protocol="sha",
            auth_key="authpass123",
            priv_protocol="aes",
            priv_key="privpass123",
        ),
    )
    try:
        with pytest.raises((CannotConnect, InvalidAuth)):
            await client.async_get_info()
    finally:
        await client.async_close()


@pytest.mark.parametrize(("auth_key", "ok"), [("authpass123", True), ("wrongpass99", False)])
async def test_snmpv3_auth_priv(
    socket_enabled: None, disable_block_async_io: None, auth_key: str, ok: bool
) -> None:
    """SHA/AES SNMPv3 against pysnmp's own agent; a wrong key is reported as such."""
    block_async_io.enable()
    values = {
        key: value
        for key, value in ap7920_values(outlets=2).items()
        if key.startswith((f"{RPDU}.1.", f"{RPDU}.2.", f"{RPDU}.3.5."))
    }
    engine, port = start_v3_agent(values, "ha", "authpass123", "privpass123")
    client = APCPDUClient(
        "127.0.0.1",
        SNMPAuth(
            version=SNMP_VERSION_3,
            username="ha",
            auth_protocol="sha",
            auth_key=auth_key,
            priv_protocol="aes",
            priv_key="privpass123",
        ),
        port=port,
        timeout=1,
        retries=0,
    )
    try:
        if ok:
            info = await client.async_get_info()
            assert (info.model, info.serial, info.outlet_count) == ("AP7920", "ZA0123456789", 2)
            status = await client.async_get_status(info)
            assert status.outlets[1].is_on is True
        else:
            with pytest.raises(InvalidAuth):
                await client.async_get_info()
    finally:
        await client.async_close()
        close_v3_agent(engine)
