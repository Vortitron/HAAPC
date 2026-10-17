"""Config, reconfigure and options flow tests."""

from __future__ import annotations

import pytest
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_SCAN_INTERVAL, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.apc_pdu.const import (
    CONF_AUTH_KEY,
    CONF_AUTH_PROTOCOL,
    CONF_COMMUNITY,
    CONF_PRIV_KEY,
    CONF_PRIV_PROTOCOL,
    CONF_SNMP_VERSION,
    DOMAIN,
)
from custom_components.apc_pdu.snmp import CannotConnect, InvalidAuth, NotSupported

from .conftest import HOST, SERIAL, FakePDU

V1_INPUT = {CONF_HOST: HOST, CONF_COMMUNITY: "private", CONF_SNMP_VERSION: "1", CONF_PORT: 161}


async def _start(hass: HomeAssistant) -> dict:
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert set(result["data_schema"].schema) == {
        CONF_HOST,
        CONF_COMMUNITY,
        CONF_SNMP_VERSION,
        CONF_PORT,
    }
    return result


async def test_user_flow_v1(hass: HomeAssistant, pdu: FakePDU) -> None:
    """A reachable PDU creates an entry named after the PDU."""
    result = await _start(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {**V1_INPUT, CONF_HOST: f" {HOST} "}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Rack A"
    assert result["data"] == V1_INPUT
    assert result["result"].unique_id == SERIAL
    assert pdu.created[0]["auth"].community == "private"
    # The probe client is closed again
    assert pdu.closed >= 1


@pytest.mark.parametrize(
    ("error", "key"),
    [
        (CannotConnect("timeout"), "cannot_connect"),
        (NotSupported("no rPDU"), "not_supported"),
        (RuntimeError("boom"), "unknown"),
    ],
)
async def test_user_flow_errors_recover(
    hass: HomeAssistant, pdu: FakePDU, error: Exception, key: str
) -> None:
    """Errors are shown on the form and the user can retry."""
    result = await _start(hass)
    pdu.info_error = error
    result = await hass.config_entries.flow.async_configure(result["flow_id"], V1_INPUT)
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": key}

    pdu.info_error = None
    result = await hass.config_entries.flow.async_configure(result["flow_id"], V1_INPUT)
    assert result["type"] is FlowResultType.CREATE_ENTRY


async def test_user_flow_snmpv3(hass: HomeAssistant, pdu: FakePDU) -> None:
    """SNMPv3 asks for credentials in a second step."""
    result = await _start(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {**V1_INPUT, CONF_SNMP_VERSION: "3"}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "snmpv3"

    v3 = {
        CONF_USERNAME: "homeassistant",
        CONF_AUTH_PROTOCOL: "sha",
        CONF_AUTH_KEY: "short",
        CONF_PRIV_PROTOCOL: "aes",
        CONF_PRIV_KEY: "privpass123",
    }
    result = await hass.config_entries.flow.async_configure(result["flow_id"], v3)
    assert result["errors"] == {CONF_AUTH_KEY: "key_too_short"}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {**v3, CONF_AUTH_PROTOCOL: "none", CONF_AUTH_KEY: ""}
    )
    assert result["errors"] == {"base": "priv_requires_auth"}

    pdu.info_error = InvalidAuth("wrongDigest")
    v3[CONF_AUTH_KEY] = "authpass123"
    result = await hass.config_entries.flow.async_configure(result["flow_id"], v3)
    assert result["errors"] == {"base": "invalid_auth"}

    pdu.info_error = None
    result = await hass.config_entries.flow.async_configure(result["flow_id"], v3)
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        CONF_HOST: HOST,
        CONF_SNMP_VERSION: "3",
        CONF_PORT: 161,
        **v3,
    }
    auth = pdu.created[-1]["auth"]
    assert (auth.username, auth.auth_protocol, auth.priv_protocol) == (
        "homeassistant",
        "sha",
        "aes",
    )


async def test_snmpv3_without_privacy(hass: HomeAssistant, pdu: FakePDU) -> None:
    """Unused passphrases are not stored."""
    result = await _start(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {**V1_INPUT, CONF_SNMP_VERSION: "3"}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_USERNAME: "ha",
            CONF_AUTH_PROTOCOL: "md5",
            CONF_AUTH_KEY: "authpass123",
            CONF_PRIV_PROTOCOL: "none",
            CONF_PRIV_KEY: "",
        },
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert CONF_PRIV_KEY not in result["data"]


async def test_same_pdu_new_address_updates_entry(hass: HomeAssistant, pdu: FakePDU) -> None:
    """Adding a PDU that is already configured updates its address."""
    entry = MockConfigEntry(
        domain=DOMAIN, unique_id=SERIAL, data={**V1_INPUT, CONF_HOST: "192.0.2.99"}, minor_version=2
    )
    entry.add_to_hass(hass)
    result = await _start(hass)
    result = await hass.config_entries.flow.async_configure(result["flow_id"], V1_INPUT)
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
    assert entry.data[CONF_HOST] == HOST


async def test_pdu_without_serial_dedupes_on_host(hass: HomeAssistant, pdu: FakePDU) -> None:
    """Without a serial number the host identifies the PDU."""
    pdu.info.serial = None
    MockConfigEntry(domain=DOMAIN, data=V1_INPUT, minor_version=2).add_to_hass(hass)
    result = await _start(hass)
    result = await hass.config_entries.flow.async_configure(result["flow_id"], V1_INPUT)
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_reconfigure(hass: HomeAssistant, pdu: FakePDU) -> None:
    """Reconfigure changes the address and reloads the entry."""
    entry = MockConfigEntry(domain=DOMAIN, unique_id=SERIAL, data=V1_INPUT, minor_version=2)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    result = await entry.start_reconfigure_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"

    pdu.info_error = CannotConnect("timeout")
    new = {**V1_INPUT, CONF_HOST: "192.0.2.20", CONF_SNMP_VERSION: "2c"}
    result = await hass.config_entries.flow.async_configure(result["flow_id"], new)
    assert result["errors"] == {"base": "cannot_connect"}

    pdu.info_error = None
    result = await hass.config_entries.flow.async_configure(result["flow_id"], new)
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert entry.data == new
    assert entry.state is config_entries.ConfigEntryState.LOADED
    assert pdu.created[-1]["host"] == "192.0.2.20"


async def test_reconfigure_to_other_pdu_aborts(hass: HomeAssistant, pdu: FakePDU) -> None:
    """Pointing an entry at a different PDU is refused."""
    entry = MockConfigEntry(domain=DOMAIN, unique_id=SERIAL, data=V1_INPUT, minor_version=2)
    entry.add_to_hass(hass)
    result = await entry.start_reconfigure_flow(hass)
    pdu.info.serial = "OTHER"
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {**V1_INPUT, CONF_HOST: "192.0.2.30"}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "wrong_device"
    assert entry.data[CONF_HOST] == HOST


async def test_reconfigure_to_snmpv3(hass: HomeAssistant, pdu: FakePDU) -> None:
    """Switching to SNMPv3 drops the community."""
    entry = MockConfigEntry(domain=DOMAIN, unique_id=SERIAL, data=V1_INPUT, minor_version=2)
    entry.add_to_hass(hass)
    result = await entry.start_reconfigure_flow(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {**V1_INPUT, CONF_SNMP_VERSION: "3"}
    )
    assert result["step_id"] == "snmpv3"
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_USERNAME: "ha",
            CONF_AUTH_PROTOCOL: "sha256",
            CONF_AUTH_KEY: "authpass123",
            CONF_PRIV_PROTOCOL: "aes256",
            CONF_PRIV_KEY: "privpass123",
        },
    )
    await hass.async_block_till_done()
    assert result["reason"] == "reconfigure_successful"
    assert CONF_COMMUNITY not in entry.data
    assert entry.data[CONF_SNMP_VERSION] == "3"


async def test_options_flow_sets_poll_interval(hass: HomeAssistant, pdu: FakePDU) -> None:
    """The poll interval option is applied to the coordinator."""
    entry = MockConfigEntry(domain=DOMAIN, unique_id=SERIAL, data=V1_INPUT, minor_version=2)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.runtime_data.update_interval.total_seconds() == 30

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert set(result["data_schema"].schema) == {CONF_SCAN_INTERVAL}
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_SCAN_INTERVAL: 120}
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert entry.options == {CONF_SCAN_INTERVAL: 120}
    assert entry.runtime_data.update_interval.total_seconds() == 120
