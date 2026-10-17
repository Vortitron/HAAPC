"""Setup, entities, switching and migration tests."""

from __future__ import annotations

from datetime import timedelta

import pytest
from homeassistant.components.switch import DOMAIN as SWITCH_DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import (
    ATTR_ENTITY_ID,
    CONF_HOST,
    CONF_PORT,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    STATE_OFF,
    STATE_ON,
    STATE_UNAVAILABLE,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
)

from custom_components.apc_pdu.const import CONF_COMMUNITY, CONF_SNMP_VERSION, DOMAIN
from custom_components.apc_pdu.snmp import (
    CannotConnect,
    CommandFailed,
    InvalidAuth,
    LoadEntry,
    OutletStatus,
)

from .conftest import HOST, SERIAL, FakePDU

DATA = {CONF_HOST: HOST, CONF_PORT: 161, CONF_SNMP_VERSION: "1", CONF_COMMUNITY: "private"}


async def _setup(hass: HomeAssistant, **kwargs) -> MockConfigEntry:
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Rack A",
        unique_id=SERIAL,
        data=kwargs.pop("data", DATA),
        minor_version=kwargs.pop("minor_version", 2),
        **kwargs,
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


def _entity_id(hass: HomeAssistant, platform: str, unique_suffix: str) -> str:
    entity_id = er.async_get(hass).async_get_entity_id(
        platform, DOMAIN, f"{SERIAL}_{unique_suffix}"
    )
    assert entity_id, unique_suffix
    return entity_id


async def test_setup_creates_device_and_entities(hass: HomeAssistant, pdu: FakePDU) -> None:
    """Every outlet becomes a switch and real readings become sensors."""
    entry = await _setup(hass)
    assert entry.state is ConfigEntryState.LOADED

    devices = dr.async_entries_for_config_entry(dr.async_get(hass), entry.entry_id)
    assert len(devices) == 1
    device = devices[0]
    assert device.identifiers == {(DOMAIN, SERIAL)}
    assert (device.manufacturer, device.model, device.serial_number) == ("APC", "AP7920", SERIAL)
    assert device.sw_version == "v3.7.3"
    assert device.name == "Rack A"

    entities = er.async_entries_for_config_entry(er.async_get(hass), entry.entry_id)
    assert all(entity.device_id == device.id for entity in entities)
    switches = sorted(e.unique_id for e in entities if e.domain == "switch")
    assert switches == sorted(
        [f"{SERIAL}_outlet_{n}" for n in range(1, 9)] + [f"{SERIAL}_master_switch"]
    )

    # Outlet 1 is named on the PDU, the others keep the default name
    router = hass.states.get(_entity_id(hass, "switch", "outlet_1"))
    assert router.state == STATE_ON
    assert router.attributes["friendly_name"] == "Rack A Router"
    assert router.attributes["outlet_number"] == 1
    assert hass.states.get(_entity_id(hass, "switch", "outlet_2")).state == STATE_OFF

    current = hass.states.get(_entity_id(hass, "sensor", "load_1_current"))
    assert current.state == "1.7"
    assert current.attributes["unit_of_measurement"] == "A"
    assert current.attributes["friendly_name"] == "Rack A Current"
    load_state = hass.states.get(_entity_id(hass, "sensor", "bank_load_state"))
    assert load_state.state == "normal"
    assert load_state.attributes["options"] == ["normal", "low", "near_overload", "overload"]
    assert hass.states.get(_entity_id(hass, "sensor", "power")).state == "380"
    assert hass.states.get(_entity_id(hass, "sensor", "rated_current")).state == "10"
    voltage = hass.states.get(_entity_id(hass, "sensor", "rated_voltage"))
    assert voltage.state == "230"
    assert voltage.attributes["friendly_name"] == "Rack A Nominal voltage"

    all_outlets = hass.states.get(_entity_id(hass, "switch", "master_switch"))
    assert all_outlets.state == STATE_ON
    assert all_outlets.attributes["friendly_name"] == "Rack A All outlets"
    assert all_outlets.attributes["outlets_on"] == 4

    # Nothing is created for values this PDU does not report
    sensors = {e.unique_id for e in entities if e.domain == "sensor"}
    assert not any("outlet_" in uid for uid in sensors)


async def test_unsupported_values_create_no_sensors(hass: HomeAssistant, pdu: FakePDU) -> None:
    """No power sensor when the PDU has no power OID."""
    pdu.info.has_power = False
    pdu.info.rated_current = None
    entry = await _setup(hass)
    uids = {
        e.unique_id for e in er.async_entries_for_config_entry(er.async_get(hass), entry.entry_id)
    }
    assert f"{SERIAL}_power" not in uids
    assert f"{SERIAL}_rated_current" not in uids


async def test_banked_and_outlet_metered_pdu(hass: HomeAssistant, pdu: FakePDU) -> None:
    """Phase/bank rows and outlet currents get distinct names."""
    pdu.info.loads = [
        LoadEntry(index=1, phase=1, bank=0),
        LoadEntry(index=2, phase=0, bank=1),
        LoadEntry(index=3, phase=0, bank=2),
    ]
    pdu.info.has_outlet_current = True
    pdu.load_current = {1: 3.1, 2: 1.9, 3: 1.2}
    pdu.load_state = {1: "normal", 2: "near_overload", 3: "low"}
    await _setup(hass)

    phase = hass.states.get(_entity_id(hass, "sensor", "load_1_current"))
    assert phase.attributes["friendly_name"] == "Rack A Phase 1 current"
    bank2 = hass.states.get(_entity_id(hass, "sensor", "load_3_current"))
    assert (bank2.state, bank2.attributes["friendly_name"]) == ("1.2", "Rack A Bank 2 current")
    bank1_state = hass.states.get(_entity_id(hass, "sensor", "load_2_state"))
    assert (bank1_state.state, bank1_state.attributes["friendly_name"]) == (
        "near_overload",
        "Rack A Bank 1 load state",
    )
    outlet = hass.states.get(_entity_id(hass, "sensor", "outlet_1_current"))
    assert (outlet.state, outlet.attributes["friendly_name"]) == ("0.1", "Rack A Router current")


async def test_switch_outlet(hass: HomeAssistant, pdu: FakePDU) -> None:
    """Turning an outlet on and off sends the SNMP command."""
    await _setup(hass)
    entity_id = _entity_id(hass, "switch", "outlet_2")

    await hass.services.async_call(
        SWITCH_DOMAIN, SERVICE_TURN_ON, {ATTR_ENTITY_ID: entity_id}, blocking=True
    )
    await hass.async_block_till_done()
    assert pdu.set_calls == [(2, True)]
    assert hass.states.get(entity_id).state == STATE_ON

    await hass.services.async_call(
        SWITCH_DOMAIN, SERVICE_TURN_OFF, {ATTR_ENTITY_ID: entity_id}, blocking=True
    )
    await hass.async_block_till_done()
    assert pdu.set_calls[-1] == (2, False)
    assert hass.states.get(entity_id).state == STATE_OFF


async def test_switch_failure_raises(hass: HomeAssistant, pdu: FakePDU) -> None:
    """A rejected command surfaces as an error and leaves the state alone."""
    await _setup(hass)
    entity_id = _entity_id(hass, "switch", "outlet_2")
    pdu.set_error = CommandFailed("noSuchName")
    with pytest.raises(HomeAssistantError, match="write access"):
        await hass.services.async_call(
            SWITCH_DOMAIN, SERVICE_TURN_ON, {ATTR_ENTITY_ID: entity_id}, blocking=True
        )
    assert hass.states.get(entity_id).state == STATE_OFF


async def test_all_outlets_switch(hass: HomeAssistant, pdu: FakePDU) -> None:
    """The all-outlets switch switches every outlet."""
    await _setup(hass)
    entity_id = _entity_id(hass, "switch", "master_switch")
    await hass.services.async_call(
        SWITCH_DOMAIN, SERVICE_TURN_OFF, {ATTR_ENTITY_ID: entity_id}, blocking=True
    )
    await hass.async_block_till_done()
    assert sorted(pdu.set_calls) == [(n, False) for n in range(1, 9)]
    assert hass.states.get(entity_id).state == STATE_OFF
    assert hass.states.get(_entity_id(hass, "switch", "outlet_1")).state == STATE_OFF

    pdu.set_calls.clear()
    await hass.services.async_call(
        SWITCH_DOMAIN, SERVICE_TURN_ON, {ATTR_ENTITY_ID: entity_id}, blocking=True
    )
    await hass.async_block_till_done()
    assert sorted(pdu.set_calls) == [(n, True) for n in range(1, 9)]
    assert hass.states.get(entity_id).attributes["outlets_on"] == 8


async def test_poll_updates_and_unavailable(hass: HomeAssistant, pdu: FakePDU) -> None:
    """Polls pick up changes made elsewhere; failures mark entities unavailable."""
    await _setup(hass)
    entity_id = _entity_id(hass, "switch", "outlet_2")
    current_id = _entity_id(hass, "sensor", "load_1_current")

    pdu.outlets[2] = True
    pdu.names[2] = "NAS"
    pdu.load_current[1] = 2.4
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=31))
    await hass.async_block_till_done()
    state = hass.states.get(entity_id)
    assert state.state == STATE_ON
    assert state.attributes["friendly_name"] == "Rack A NAS"
    assert hass.states.get(current_id).state == "2.4"

    pdu.status_error = CannotConnect("timeout")
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=62))
    await hass.async_block_till_done()
    assert hass.states.get(entity_id).state == STATE_UNAVAILABLE
    assert hass.states.get(current_id).state == STATE_UNAVAILABLE

    pdu.status_error = None
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=93))
    await hass.async_block_till_done()
    assert hass.states.get(entity_id).state == STATE_ON


async def test_outlet_without_state_is_unavailable(hass: HomeAssistant, pdu: FakePDU) -> None:
    """An outlet the PDU stops reporting is unavailable, not off."""
    await _setup(hass)
    original = pdu.status

    def partial_status():
        status = original()
        status.outlets[3] = OutletStatus(name=None, is_on=None)
        return status

    pdu.status = partial_status
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=31))
    await hass.async_block_till_done()
    assert hass.states.get(_entity_id(hass, "switch", "outlet_3")).state == STATE_UNAVAILABLE


@pytest.mark.parametrize(
    ("error", "state"),
    [
        (CannotConnect("timeout"), ConfigEntryState.SETUP_RETRY),
        (InvalidAuth("wrongDigest"), ConfigEntryState.SETUP_ERROR),
    ],
)
async def test_setup_errors(
    hass: HomeAssistant, pdu: FakePDU, error: Exception, state: ConfigEntryState
) -> None:
    """Unreachable PDUs are retried; rejected credentials are not."""
    pdu.info_error = error
    entry = await _setup(hass)
    assert entry.state is state
    assert pdu.closed == 1


async def test_first_poll_failure_retries(hass: HomeAssistant, pdu: FakePDU) -> None:
    """A failing first poll retries setup and closes the client."""
    pdu.status_error = CannotConnect("timeout")
    entry = await _setup(hass)
    assert entry.state is ConfigEntryState.SETUP_RETRY
    assert pdu.closed == 1


async def test_unload_closes_client(hass: HomeAssistant, pdu: FakePDU) -> None:
    """Unloading releases the SNMP engine."""
    entry = await _setup(hass)
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.NOT_LOADED
    assert pdu.closed == 1


async def test_migrate_1_0_entry(hass: HomeAssistant, pdu: FakePDU) -> None:
    """1.0.x entries are migrated and their obsolete entities removed."""
    registry = er.async_get(hass)
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="My PDU",
        unique_id=SERIAL,
        data={
            CONF_HOST: HOST,
            CONF_COMMUNITY: "private",
            CONF_SNMP_VERSION: "1",
            "name": "My PDU",
            "demo_mode": False,
        },
        minor_version=1,
    )
    entry.add_to_hass(hass)
    kept = registry.async_get_or_create(
        "switch",
        DOMAIN,
        f"{SERIAL}_outlet_1",
        config_entry=entry,
        suggested_object_id="my_pdu_outlet_1",
    )
    stale = [
        registry.async_get_or_create("sensor", DOMAIN, f"{SERIAL}_{suffix}", config_entry=entry)
        for suffix in (
            "outlet_count",
            "firmware",
            "hardware",
            "rated_max_current",
            "outlet_3_power",
        )
    ]

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.LOADED
    assert entry.minor_version == 2
    assert entry.data == DATA
    # Existing entity IDs survive the update
    assert hass.states.get("switch.my_pdu_outlet_1").state == STATE_ON
    assert registry.async_get(kept.entity_id) is not None
    for entity in stale:
        assert registry.async_get(entity.entity_id) is None
