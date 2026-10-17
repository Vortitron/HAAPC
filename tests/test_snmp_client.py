"""Run the real pysnmp client against a fake APC agent on 127.0.0.1."""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
from homeassistant import block_async_io

from custom_components.apc_pdu.const import (
    SNMP_VERSION_1,
    SNMP_VERSION_2C,
    SNMP_VERSION_3,
)
from custom_components.apc_pdu.snmp import (
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
    FakeAPCAgent,
    ap7920_values,
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
    """A device without the rPDU MIB is rejected."""
    agent.values.clear()
    agent.values["1.3.6.1.2.1.1.1.0"] = "Some switch"
    client = await _client(agent, SNMPAuth(version=SNMP_VERSION_1, community="public"))
    try:
        with pytest.raises(NotSupported):
            await client.async_get_info()
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
