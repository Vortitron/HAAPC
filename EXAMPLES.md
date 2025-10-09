# Usage Examples

This document provides practical examples for using the APC PDU integration in Home Assistant.

## Basic Usage

### Dashboard Card - Outlet Controls

```yaml
type: entities
title: Server Room PDU
entities:
  - entity: switch.apc_pdu_outlet_1
    name: Server 1
  - entity: switch.apc_pdu_outlet_2
    name: Server 2
  - entity: switch.apc_pdu_outlet_3
    name: Network Switch
  - entity: switch.apc_pdu_outlet_4
    name: Router
  - entity: switch.apc_pdu_master_switch
    name: Master Control
```

### Dashboard Card - Power Monitoring

```yaml
type: entities
title: Power Consumption
entities:
  - entity: sensor.apc_pdu_outlet_1_power
    name: Server 1
  - entity: sensor.apc_pdu_outlet_2_power
    name: Server 2
  - entity: sensor.apc_pdu_outlet_3_power
    name: Network Switch
  - type: attribute
    entity: switch.apc_pdu_master_switch
    attribute: total_power_w
    name: Total Power
```

### Glance Card - Quick Overview

```yaml
type: glance
title: PDU Status
entities:
  - entity: switch.apc_pdu_outlet_1
  - entity: switch.apc_pdu_outlet_2
  - entity: switch.apc_pdu_outlet_3
  - entity: switch.apc_pdu_outlet_4
  - entity: sensor.apc_pdu_bank_load_state
```

## Automations

### Turn Everything On/Off on Schedule

```yaml
# Morning - Turn on all outlets
automation:
  - alias: "PDU - Morning Power On"
    trigger:
      - platform: time
        at: "07:00:00"
    action:
      - service: switch.turn_on
        target:
          entity_id: switch.apc_pdu_master_switch

# Night - Turn off all outlets
  - alias: "PDU - Night Power Off"
    trigger:
      - platform: time
        at: "23:00:00"
    action:
      - service: switch.turn_off
        target:
          entity_id: switch.apc_pdu_master_switch
```

### Staggered Startup (Prevent Power Surge)

```yaml
automation:
  - alias: "PDU - Staggered Startup"
    trigger:
      - platform: state
        entity_id: input_boolean.start_servers
        to: "on"
    action:
      - service: switch.turn_on
        target:
          entity_id: switch.apc_pdu_outlet_1
      - delay: "00:00:30"
      - service: switch.turn_on
        target:
          entity_id: switch.apc_pdu_outlet_2
      - delay: "00:00:30"
      - service: switch.turn_on
        target:
          entity_id: switch.apc_pdu_outlet_3
      - delay: "00:00:30"
      - service: switch.turn_on
        target:
          entity_id: switch.apc_pdu_outlet_4
```

### High Power Alert

```yaml
automation:
  - alias: "PDU - High Power Alert"
    trigger:
      - platform: numeric_state
        entity_id: switch.apc_pdu_master_switch
        attribute: total_power_w
        above: 1500
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "PDU High Power Usage"
          message: >
            PDU is drawing {{ state_attr('switch.apc_pdu_master_switch', 'total_power_w') }}W
          data:
            priority: high
```

### Overload Protection

```yaml
automation:
  - alias: "PDU - Overload Protection"
    trigger:
      - platform: state
        entity_id: sensor.apc_pdu_bank_load_state
        to: "Overload"
    action:
      - service: notify.persistent_notification.create
        data:
          title: "⚠️ PDU OVERLOAD"
          message: "PDU is in overload state! Consider turning off some outlets."
      - service: notify.mobile_app_your_phone
        data:
          title: "PDU Overload"
          message: "Critical: PDU overload detected!"
          data:
            priority: critical
```

### Per-Outlet Power Tracking

```yaml
automation:
  - alias: "PDU - Track Outlet 1 Power"
    trigger:
      - platform: state
        entity_id: sensor.apc_pdu_outlet_1_power
    condition:
      - condition: template
        value_template: "{{ trigger.to_state.state | float(0) > 0 }}"
    action:
      - service: logbook.log
        data:
          name: Server 1
          message: "Power: {{ states('sensor.apc_pdu_outlet_1_power') }}W"
          entity_id: sensor.apc_pdu_outlet_1_power
```

### Auto-Reboot on Device Hang

```yaml
automation:
  - alias: "PDU - Auto Reboot Server on Hang"
    trigger:
      - platform: state
        entity_id: binary_sensor.server_1_ping
        to: "off"
        for: "00:05:00"
    action:
      - service: switch.turn_off
        target:
          entity_id: switch.apc_pdu_outlet_1
      - delay: "00:00:10"
      - service: switch.turn_on
        target:
          entity_id: switch.apc_pdu_outlet_1
      - service: notify.mobile_app_your_phone
        data:
          message: "Server 1 was unresponsive and has been rebooted"
```

### Energy Cost Calculation

```yaml
# Template sensor for daily energy cost
template:
  - sensor:
      - name: "PDU Daily Energy Cost"
        unit_of_measurement: "USD"
        state: >
          {% set total_power = state_attr('switch.apc_pdu_master_switch', 'total_power_w') | float(0) %}
          {% set kwh_per_day = (total_power / 1000) * 24 %}
          {% set cost_per_kwh = 0.12 %}
          {{ (kwh_per_day * cost_per_kwh) | round(2) }}
        icon: mdi:currency-usd
```

## Scripts

### Controlled Shutdown Sequence

```yaml
script:
  pdu_shutdown_sequence:
    alias: "PDU Shutdown Sequence"
    sequence:
      - service: notify.mobile_app_your_phone
        data:
          message: "Starting PDU shutdown sequence"
      # Turn off servers first
      - service: switch.turn_off
        target:
          entity_id:
            - switch.apc_pdu_outlet_1
            - switch.apc_pdu_outlet_2
      - delay: "00:01:00"
      # Then network equipment
      - service: switch.turn_off
        target:
          entity_id:
            - switch.apc_pdu_outlet_3
            - switch.apc_pdu_outlet_4
      - service: notify.mobile_app_your_phone
        data:
          message: "PDU shutdown complete"
```

### Emergency All Off

```yaml
script:
  pdu_emergency_off:
    alias: "PDU Emergency All Off"
    sequence:
      - service: switch.turn_off
        target:
          entity_id: switch.apc_pdu_master_switch
      - service: notify.mobile_app_your_phone
        data:
          title: "Emergency Shutdown"
          message: "PDU all outlets turned off"
          data:
            priority: critical
```

## Advanced Dashboards

### Comprehensive PDU Dashboard

```yaml
type: vertical-stack
cards:
  # Status Overview
  - type: entities
    title: PDU Status
    entities:
      - entity: sensor.apc_pdu_bank_load_state
        name: Load State
      - type: attribute
        entity: switch.apc_pdu_master_switch
        attribute: total_power_w
        name: Total Power
      - type: attribute
        entity: switch.apc_pdu_master_switch
        attribute: outlets_on
        name: Active Outlets
      - entity: sensor.apc_pdu_rated_voltage
      - entity: sensor.apc_pdu_rated_max_current

  # Master Control
  - type: entities
    title: Master Control
    entities:
      - entity: switch.apc_pdu_master_switch

  # Individual Outlets
  - type: entities
    title: Outlets
    entities:
      - type: custom:fold-entity-row
        head:
          type: section
          label: "Outlet 1 - Server 1"
        entities:
          - entity: switch.apc_pdu_outlet_1
          - entity: sensor.apc_pdu_outlet_1_power
      - type: custom:fold-entity-row
        head:
          type: section
          label: "Outlet 2 - Server 2"
        entities:
          - entity: switch.apc_pdu_outlet_2
          - entity: sensor.apc_pdu_outlet_2_power
      # ... repeat for other outlets

  # Power Graph
  - type: history-graph
    title: Power Consumption
    hours_to_show: 24
    entities:
      - entity: sensor.apc_pdu_outlet_1_power
      - entity: sensor.apc_pdu_outlet_2_power
      - entity: sensor.apc_pdu_outlet_3_power
      - entity: sensor.apc_pdu_outlet_4_power
```

### Mobile-Friendly Card

```yaml
type: vertical-stack
cards:
  - type: glance
    title: PDU Quick Control
    show_name: true
    show_state: true
    entities:
      - entity: switch.apc_pdu_outlet_1
        name: Srv1
      - entity: switch.apc_pdu_outlet_2
        name: Srv2
      - entity: switch.apc_pdu_outlet_3
        name: Net
      - entity: switch.apc_pdu_outlet_4
        name: Rtr
  - type: button
    entity: switch.apc_pdu_master_switch
    name: All On/Off
    show_state: true
    tap_action:
      action: toggle
```

## Node-RED Examples

### Flow for Intelligent Load Management

```json
[
    {
        "id": "pdu_load_check",
        "type": "server-state-changed",
        "name": "Monitor Total Power",
        "server": "home_assistant",
        "entityidfilter": "switch.apc_pdu_master_switch",
        "entityidfiltertype": "exact",
        "outputinitially": false,
        "state_type": "str",
        "outputs": 1
    },
    {
        "id": "check_power_threshold",
        "type": "switch",
        "name": "Check if > 1200W",
        "property": "data.attributes.total_power_w",
        "rules": [
            {
                "t": "gt",
                "v": "1200",
                "vt": "num"
            }
        ],
        "outputs": 1
    },
    {
        "id": "turn_off_non_critical",
        "type": "call-service",
        "name": "Turn Off Outlet 4",
        "server": "home_assistant",
        "service": "switch.turn_off",
        "data": "{\"entity_id\":\"switch.apc_pdu_outlet_4\"}"
    }
]
```

## Tips & Tricks

### Get Outlet Names Programmatically

```python
# In a Python script or AppDaemon
outlets = {}
for i in range(1, 9):
    outlet_entity = f"switch.apc_pdu_outlet_{i}"
    outlet_name = hass.states.get(outlet_entity).attributes.get('outlet_name')
    outlets[i] = outlet_name
```

### Template for Dynamic Entity Naming

```yaml
# Rename outlets based on their configured names
customize:
  switch.apc_pdu_outlet_1:
    friendly_name: "{{ state_attr('switch.apc_pdu_outlet_1', 'outlet_name') }}"
```

### Use with Alexa/Google Home

Add outlets to your voice assistant:
```yaml
# configuration.yaml
alexa:
  smart_home:
    filter:
      include_entities:
        - switch.apc_pdu_outlet_1
        - switch.apc_pdu_outlet_2
        - switch.apc_pdu_master_switch
```

Then say: "Alexa, turn on Server 1" (if outlet 1 is named "Server 1")

## Need More Help?

See the [README](README.md) for more information or [open an issue](https://github.com/vortitron/HAAPC/issues) with your use case!

