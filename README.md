# APC PDU for Home Assistant

[![HACS](https://img.shields.io/badge/HACS-Integration-41BDF5.svg)](https://hacs.xyz)
[![Validate](https://github.com/Vortitron/HAAPC/actions/workflows/validate.yml/badge.svg)](https://github.com/Vortitron/HAAPC/actions/workflows/validate.yml)

Control and monitor APC Switched Rack PDUs (AP7920 and the rest of the AP79xx
family) from Home Assistant over SNMP. Every outlet becomes a switch and the
PDU's load readings become sensors, all grouped under one device.

## Supported devices

APC rack PDUs that implement the `rPDU` branch of the APC PowerNet MIB
(`.1.3.6.1.4.1.318.1.1.12`), which is the first-generation Switched Rack PDU
range (AP79xx). It has been used with an AP7920; other AP79xx models use the
same MIB and are expected to work. PDUs that only implement the newer `rPDU2`
branch (for example many AP8xxx models) are not supported yet; setup reports
that the device does not provide the APC rPDU MIB.

SNMPv1, SNMPv2c and SNMPv3 are supported.

## Installation

### HACS

Search for **APC PDU** in HACS, download it and restart Home Assistant.

If it is not listed yet, add `https://github.com/Vortitron/HAAPC` as a custom
repository of type *Integration* first.

### Manual

Copy `custom_components/apc_pdu` into the `custom_components` folder of your
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

*Settings > Devices & services > Add integration > APC PDU*

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
| Power | Total watts, only if the PDU reports it |
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
    custom_components.apc_pdu: debug
```

### OIDs used

All under `.1.3.6.1.4.1.318.1.1.12` (PowerNet-MIB `rPDU`):

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
