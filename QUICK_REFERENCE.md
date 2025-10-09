# Quick Reference Card

## 📋 Entity IDs (After Installation)

### Switches
```
switch.apc_pdu_outlet_1          # Outlet 1
switch.apc_pdu_outlet_2          # Outlet 2
switch.apc_pdu_outlet_3          # Outlet 3
switch.apc_pdu_outlet_4          # Outlet 4
switch.apc_pdu_outlet_5          # Outlet 5
switch.apc_pdu_outlet_6          # Outlet 6
switch.apc_pdu_outlet_7          # Outlet 7
switch.apc_pdu_outlet_8          # Outlet 8
switch.apc_pdu_master_switch     # All outlets
```

### Power Sensors
```
sensor.apc_pdu_outlet_1_power    # Outlet 1 power (W)
sensor.apc_pdu_outlet_2_power    # Outlet 2 power (W)
... (etc for all 8 outlets)
```

### PDU Sensors
```
sensor.apc_pdu_rated_voltage     # Rated voltage (V)
sensor.apc_pdu_rated_max_current # Max current (A)
sensor.apc_pdu_bank_load_state   # Load state
sensor.apc_pdu_outlet_count      # Number of outlets
sensor.apc_pdu_hardware_version  # Hardware version
sensor.apc_pdu_firmware_version  # Firmware version
```

## 🔌 Switch Attributes

### Individual Outlet Switch
```yaml
outlet_number: 1
outlet_name: "Server 1"
power_w: 145
```

### Master Switch
```yaml
total_outlets: 8
outlets_on: 5
total_power_w: 847
rated_voltage: 120
rated_max_current: 20.0
bank_load_state: "Normal"
```

## 🎯 Common Automations

### Turn On/Off at Specific Time
```yaml
automation:
  - alias: "PDU On at 7am"
    trigger:
      platform: time
      at: "07:00:00"
    action:
      service: switch.turn_on
      target:
        entity_id: switch.apc_pdu_master_switch
```

### High Power Alert
```yaml
automation:
  - alias: "High Power Alert"
    trigger:
      platform: numeric_state
      entity_id: switch.apc_pdu_master_switch
      attribute: total_power_w
      above: 1000
    action:
      service: notify.notify
      data:
        message: "High power: {{ state_attr('switch.apc_pdu_master_switch', 'total_power_w') }}W"
```

### Control Based on Outlet Power
```yaml
automation:
  - alias: "Server 1 Power Check"
    trigger:
      platform: numeric_state
      entity_id: sensor.apc_pdu_outlet_1_power
      above: 500
    action:
      service: notify.notify
      data:
        message: "Server 1 using high power"
```

## 📊 Dashboard Cards

### Simple Control Card
```yaml
type: entities
entities:
  - switch.apc_pdu_outlet_1
  - switch.apc_pdu_outlet_2
  - switch.apc_pdu_master_switch
```

### With Power Display
```yaml
type: entities
entities:
  - entity: switch.apc_pdu_outlet_1
    secondary_info: attribute
    attribute: power_w
  - entity: switch.apc_pdu_outlet_2
    secondary_info: attribute
    attribute: power_w
```

### Glance Card
```yaml
type: glance
entities:
  - switch.apc_pdu_outlet_1
  - switch.apc_pdu_outlet_2
  - switch.apc_pdu_outlet_3
  - switch.apc_pdu_outlet_4
```

## 🔧 Service Calls

### Turn Outlet On
```yaml
service: switch.turn_on
target:
  entity_id: switch.apc_pdu_outlet_1
```

### Turn Outlet Off
```yaml
service: switch.turn_off
target:
  entity_id: switch.apc_pdu_outlet_1
```

### Toggle Outlet
```yaml
service: switch.toggle
target:
  entity_id: switch.apc_pdu_outlet_1
```

### Turn All On
```yaml
service: switch.turn_on
target:
  entity_id: switch.apc_pdu_master_switch
```

### Turn All Off
```yaml
service: switch.turn_off
target:
  entity_id: switch.apc_pdu_master_switch
```

## 📝 Templates

### Get Total Power
```jinja
{{ state_attr('switch.apc_pdu_master_switch', 'total_power_w') }}
```

### Get Outlets On Count
```jinja
{{ state_attr('switch.apc_pdu_master_switch', 'outlets_on') }}
```

### Get Specific Outlet Power
```jinja
{{ states('sensor.apc_pdu_outlet_1_power') }}
```

### Get Outlet Name
```jinja
{{ state_attr('switch.apc_pdu_outlet_1', 'outlet_name') }}
```

### Check if Any Outlet is On
```jinja
{{ state_attr('switch.apc_pdu_master_switch', 'outlets_on') | int > 0 }}
```

## 🛠️ SNMP Configuration

### Required Settings
- **Protocol**: SNMPv1 or SNMPv2c
- **Port**: 161 (default)
- **Community**: Read-write access required
- **Access Type**: Read-Write (not read-only)

### Test SNMP (Linux/Mac)
```bash
# Get model number
snmpget -v1 -c YOUR_COMMUNITY YOUR_IP .1.3.6.1.4.1.318.1.1.12.1.5.0

# Get outlet 1 status
snmpget -v1 -c YOUR_COMMUNITY YOUR_IP .1.3.6.1.4.1.318.1.1.12.3.5.1.1.4.1

# Turn outlet 1 on
snmpset -v1 -c YOUR_COMMUNITY YOUR_IP .1.3.6.1.4.1.318.1.1.12.3.3.1.1.4.1 i 1

# Turn outlet 1 off
snmpset -v1 -c YOUR_COMMUNITY YOUR_IP .1.3.6.1.4.1.318.1.1.12.3.3.1.1.4.1 i 2
```

## 📁 File Locations

### Integration Files
```
/config/custom_components/apc_pdu/
```

### HACS Installation
```
/config/custom_components/apc_pdu/
```

### Configuration
- No YAML needed!
- All configuration via UI
- Settings → Devices & Services

## 🔍 Troubleshooting

### Integration Not Found
```bash
# Check files exist
ls -la /config/custom_components/apc_pdu/

# Check manifest
cat /config/custom_components/apc_pdu/manifest.json

# Restart Home Assistant
ha core restart
```

### Cannot Connect
```bash
# Ping PDU
ping YOUR_PDU_IP

# Test SNMP
snmpget -v1 -c YOUR_COMMUNITY YOUR_PDU_IP .1.3.6.1.4.1.318.1.1.12.1.5.0

# Check firewall (allow UDP 161)
sudo ufw allow 161/udp
```

### No Power Data
- Verify PDU model supports power monitoring
- Check outlets are actually drawing power
- Try different MIB OIDs if needed

## 📞 Getting Help

1. **Check Logs**: Settings → System → Logs
2. **Enable Debug**: See INSTALLATION.md
3. **GitHub Issues**: https://github.com/vortitron/HAAPC/issues
4. **Documentation**: README.md, QUICKSTART.md, EXAMPLES.md

## ⚡ Tips & Tricks

### Use Attributes in Automations
```yaml
trigger:
  platform: template
  value_template: >
    {{ state_attr('switch.apc_pdu_master_switch', 'total_power_w') | int > 1000 }}
```

### Create Power Usage Template Sensor
```yaml
template:
  - sensor:
      - name: "PDU Power Usage"
        unit_of_measurement: "W"
        state: >
          {{ state_attr('switch.apc_pdu_master_switch', 'total_power_w') }}
```

### Group Outlets
```yaml
group:
  server_outlets:
    name: "Server Outlets"
    entities:
      - switch.apc_pdu_outlet_1
      - switch.apc_pdu_outlet_2
```

---

**Keep this handy for quick reference!** 📌

