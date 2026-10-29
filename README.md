# APC PDU Manager for Home Assistant

[![HACS](https://img.shields.io/badge/HACS-Integration-41BDF5.svg)](https://hacs.xyz)
[![Validate](https://github.com/Vortitron/HAAPC/actions/workflows/validate.yml/badge.svg)](https://github.com/Vortitron/HAAPC/actions/workflows/validate.yml)

Control and monitor APC Switched Rack PDUs (AP7920 and the rest of the AP79xx
family) from Home Assistant over SNMP. Every outlet becomes a switch and the
PDU's load readings become sensors, all grouped under one device.

## Supported devices

APC switched PDUs, through whichever branch of the APC PowerNet MIB they
implement. Setup works this out by itself:

| Branch | PDUs | What you get |
| --- | --- | --- |
| `rPDU` (`.1.3.6.1.4.1.318.1.1.12`) | First-generation Switched Rack PDUs, AP79xx | Outlets, current and load state per phase/bank, power and outlet current where the model has them |
| `rPDU2` (`.1.3.6.1.4.1.318.1.1.26`) | Switched Rack PDUs AP84xx, AP86xx, AP88xx and AP89xx | As rPDU, plus measured phase voltage and the PDU's energy meter (kWh) |
| `sPDU` (`.1.3.6.1.4.1.318.1.1.4`) | MasterSwitch units that predate rPDU (AP92xx, AP96xx) | Outlets only; these report no load |

The rPDU branch has been used with an AP7920. rPDU2 and sPDU support is built
and tested against the MIB definitions but not yet on real hardware; please
open an issue with your model if something reads wrong.

With daisy-chained rPDU2 PDUs, an entry covers the PDU at the address you add;
the PDUs chained behind it are not included. Metered-only PDUs, which have no
switched outlets, are not supported.

SNMPv1, SNMPv2c and SNMPv3 are supported.

## Installation

### HACS

Search for **APC PDU Manager** in HACS, download it and restart Home Assistant.

If it is not listed yet, add `https://github.com/Vortitron/HAAPC` as a custom
repository of type *Integration* first.

### Manual

Copy `custom_components/apc_pdu_manager` into the `custom_components` folder of your
Home Assistant configuration and restart Home Assistant.

## Preparing the PDU

In the PDU's web interface (or over telnet/SSH):

1. Enable SNMP (*Administration > Network > SNMPv1* or *SNMPv3*).
2. For SNMPv1/v2c, set up a community with **Write** access and, ideally, limit
   it to Home Assistant's IP address. A read-only community shows the outlets but
   cannot switch them.
3. For SNMPv3, create a user with an authentication passphrase (and a privacy
   passphrase if you want encryption) and give it write access.

## Configuration

*Settings > Devices & services > Add integration > APC PDU Manager*

| Field | Description |
| --- | --- |
| Host | IP address or host name of the PDU |
| Community | SNMPv1/v2c community; `private` is APC's default write community |
| SNMP version | SNMPv1 (default), SNMPv2c or SNMPv3 |
| Port | UDP port, normally 161 |

Choosing SNMPv3 opens a second step for the user name, the authentication
protocol and passphrase, and the privacy protocol and passphrase.

During setup the integration reads the model, serial number, number of outlets
and which readings the PDU supports, and names the entry after the PDU.

- **Options** (*Configure*): polling interval, 10 to 3600 seconds (default 30).
- **Reconfigure** (entry menu): change the address, community, SNMP version or
  SNMPv3 credentials. Pointing an entry at a different PDU is refused.

## Entities

| Entity | Notes |
| --- | --- |
| One switch per outlet | Named after the outlet name configured on the PDU |
| All outlets switch | On while any outlet is on; turning it on/off switches every outlet |
| Current | Measured load in amps. Banked or multi-phase PDUs get one sensor per phase and bank |
| Load state | `normal`, `low`, `near_overload` or `overload`, as judged by the PDU's own thresholds |
| Voltage | Measured volts per phase (rPDU2) |
| Power | Total watts, only if the PDU reports it |
| Energy | The PDU's own kWh meter (rPDU2). Reset on the PDU, it starts again from zero, which the Energy dashboard handles |
| Outlet current | Per-outlet amps, only on outlet-metered PDUs |
| Rated current, Nominal voltage | Diagnostic values read from the PDU |

Readings the PDU does not provide are not created at all, so no sensor shows a
made-up value.

> **Careful with the all-outlets switch.** If Home Assistant itself, its network
> switch or router is plugged into the PDU, turning it off cuts power to them
> too. Disable the entity if you do not need it.

## Example automations

Power-cycle a router every night:

```yaml
automation:
  - alias: "Reboot router nightly"
    triggers:
      - trigger: time
        at: "03:00:00"
    actions:
      - action: switch.turn_off
        target:
          entity_id: switch.rack_a_router
      - delay: "00:00:30"
      - action: switch.turn_on
        target:
          entity_id: switch.rack_a_router
```

Warn when the PDU approaches overload:

```yaml
automation:
  - alias: "PDU near overload"
    triggers:
      - trigger: state
        entity_id: sensor.rack_a_load_state
        to: ["near_overload", "overload"]
    actions:
      - action: notify.notify
        data:
          message: "PDU load is {{ states('sensor.rack_a_current') }} A ({{ trigger.to_state.state }})"
```

Stagger start-up to avoid an inrush spike:

```yaml
script:
  pdu_staggered_start:
    sequence:
      - repeat:
          for_each:
            - switch.rack_a_outlet_1
            - switch.rack_a_outlet_2
            - switch.rack_a_outlet_3
          sequence:
            - action: switch.turn_on
              target:
                entity_id: "{{ repeat.item }}"
            - delay: 5
```

Entity IDs depend on your PDU and outlet names; check yours under the device.

## Troubleshooting

**"No answer from the PDU"**: a PDU silently ignores requests with a wrong
community, so a wrong community looks exactly like an unreachable PDU. Check the
address, the SNMP version and the community, and that the PDU's SNMP access list
allows Home Assistant's IP. From a machine with net-snmp installed:

```bash
snmpget -v1 -c <community> <pdu-ip> .1.3.6.1.4.1.318.1.1.12.1.5.0   # model, e.g. "AP7920"
snmpget -v1 -c <community> <pdu-ip> .1.3.6.1.4.1.318.1.1.12.3.5.1.1.4.1   # outlet 1: 1 = on, 2 = off
```

**Outlets show but cannot be switched**: the community or SNMPv3 user has no
write access. Home Assistant reports "The PDU did not switch ...".

**Debug logging**:

```yaml
logger:
  logs:
    custom_components.apc_pdu_manager: debug
```

### OIDs used

`rPDU`, all under `.1.3.6.1.4.1.318.1.1.12`:

| OID | Object |
| --- | --- |
| `.1.1.0` / `.1.2.0` / `.1.3.0` / `.1.5.0` / `.1.6.0` | name, hardware rev., firmware rev., model, serial |
| `.1.7.0` | device rating (A) |
| `.1.8.0` | number of outlets |
| `.1.15.0` | line voltage setting (V) |
| `.1.16.0` | power (W), not on every model |
| `.2.1.2.0` / `.2.1.4.0` | number of phases / banks |
| `.2.3.1.1.2.N` / `.2.3.1.1.3.N` | phase/bank load (0.1 A) / load state |
| `.3.1.5.0` | number of monitored outlets |
| `.3.3.1.1.4.N` | outlet command (1 = on, 2 = off) |
| `.3.5.1.1.2.N` / `.3.5.1.1.4.N` / `.3.5.1.1.7.N` | outlet name / state / load (0.1 A) |

`rPDU2`, all under `.1.3.6.1.4.1.318.1.1.26`. Tables are indexed by row; the
module column says which chained PDU a row belongs to:

| OID | Object |
| --- | --- |
| `.2.1.2.1` / `.3.1` / `.5.1` / `.6.1` / `.8.1` / `.9.1` | module, name, hardware rev., firmware rev., model, serial |
| `.4.2.1.5.1` / `.4.2.1.6.1` / `.4.2.1.9.1` | switched outlets / metered outlets / max current (A) |
| `.4.3.1.5.1` / `.4.3.1.9.1` | power (0.01 kW) / energy (0.1 kWh); -1 when not measured |
| `.5.0` / `.7.0` / `.9.1.0` / `.9.3.0` | phase / bank / switched outlet / metered outlet table sizes |
| `.6.3.1.2–.6.R` | phase module, number, load state, current (0.1 A), voltage (V) |
| `.8.3.1.2–.5.R` | bank module, number, load state, current (0.1 A) |
| `.9.2.3.1.2–.5.R` | outlet module, name, number, state (1 = off, 2 = on) |
| `.9.2.4.1.5.R` | outlet command (1 = on, 2 = off) |
| `.9.4.3.1.2` / `.4` / `.6.R` | metered outlet module, number, current (0.1 A) |

`sPDU`, all under `.1.3.6.1.4.1.318.1.1.4`:

| OID | Object |
| --- | --- |
| `.1.1.0` / `.1.2.0` / `.1.4.0` / `.1.5.0` | hardware rev., firmware rev., model, serial |
| `.4.1.0` | number of outlets |
| `.4.2.1.3.N` | outlet state on read, command on write (1 = on, 2 = off) |
| `.4.2.1.4.N` | outlet name |

## Upgrading from 1.1.x

1.2.0 renames the integration from `apc_pdu` to `apc_pdu_manager` (shown as
*APC PDU Manager*). Another integration in the HACS store already uses
`apc_pdu`, and two integrations sharing a domain install into the same folder
and overwrite each other.

Home Assistant cannot carry a config entry from one domain to another, so the
PDU is added again once:

1. *Settings > Devices & services > APC PDU*: delete the PDU. This also deletes
   its entities, which frees their entity IDs.
2. Update the integration in HACS (or replace `custom_components/apc_pdu` with
   `custom_components/apc_pdu_manager`), delete the old
   `custom_components/apc_pdu` folder and restart Home Assistant.
3. Add *APC PDU Manager* with the same host and community.

The entities come back with their default entity IDs, the same ones 1.1 gave
them, so history, dashboards and automations carry on. Anything you changed in
Home Assistant itself (a renamed entity ID, a name, area or icon) needs setting
again. If you enabled debug logging, change the
logger to `custom_components.apc_pdu_manager`.

## Upgrading from 1.0.x

- Demo mode has been removed. It fell back to simulated values when the PDU did
  not answer, so a real installation could show invented readings.
- Removed sensors: *Outlet count*, *Hardware version* and *Firmware version*
  (now on the device page), *Rated max current* (it actually showed the power
  factor setting) and *Outlet N power* (it showed outlet current, in tenths of an
  amp, as watts). Home Assistant deletes these entities on the first start.
- New: measured *Current*, *Power* (where supported), per-outlet current on
  metered PDUs, SNMPv3, a configurable port, reconfiguration and a polling
  interval option.
- Outlet switches, the all-outlets switch, *Load state* and *Nominal voltage*
  (formerly *Rated voltage*) keep their entity IDs. Load state values are now
  `normal`, `low`, `near_overload` and `overload`; 1.0.x swapped normal and low.

## Development

```bash
pip install -r requirements_test.txt
pytest tests
```

The tests run the config flow and entities against a real Home Assistant core
with the SNMP client replaced, and run the real SNMP client against a small
SNMPv1/v2c agent on 127.0.0.1 that answers like an AP7920.

## License

MIT, see [LICENSE](LICENSE).
