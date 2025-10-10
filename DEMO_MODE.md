# Demo Mode - Test Without Hardware

The APC PDU integration now includes a **Demo Mode** for testing without actual hardware!

## What is Demo Mode?

Demo Mode creates a **simulated APC PDU** that behaves just like the real thing, but doesn't require:
- ❌ Actual PDU hardware
- ❌ Network connectivity to a PDU
- ❌ SNMP configuration

Perfect for:
- ✅ Testing the integration on a cloud server
- ✅ Development and debugging
- ✅ Demonstrations
- ✅ Learning Home Assistant automations

## How to Enable Demo Mode

### Option 1: During Initial Setup

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for **"APC PDU"**
4. Enter any values (they don't need to be real):
   - **IP Address**: `192.168.1.100` (can be anything)
   - **SNMP Community**: `demo` (can be anything)
   - **Device Name**: `Demo PDU` (optional)
   - **SNMP Version**: `1`
   - **Demo Mode**: ✅ **Check this box!**
5. Click **Submit**

### Option 2: Modify Config Entry

If you already have the integration installed, you can enable demo mode by editing your configuration:

1. Edit `.storage/core.config_entries` in your HA config directory
2. Find the `apc_pdu` entry
3. Add `"demo_mode": true` to the `data` section
4. Restart Home Assistant

## What You Get in Demo Mode

### Simulated Device
- **Model**: AP7920 (Demo)
- **Serial Number**: DEMO-192-168-1-100 (based on IP)
- **Firmware**: v3.7.4 (Demo)
- **Hardware**: v05 (Demo)
- **Outlets**: 8

### Simulated Outlets
All 8 outlets with realistic names:
1. Server 1 (~145W when on)
2. Server 2 (~180W when on)
3. Network Switch (~45W when on)
4. Router (~25W when on)
5. NAS (~90W when on)
6. Workstation (~120W when on)
7. Monitor (~60W when on)
8. Misc Device (~35W when on)

### Features That Work
- ✅ **Turn outlets on/off** - State is remembered
- ✅ **Master switch** - Controls all outlets
- ✅ **Power monitoring** - Shows simulated power values
- ✅ **Realistic power usage** - Different for each outlet
- ✅ **Power variation** - Values change slightly (±10%)
- ✅ **Load state** - Changes based on how many outlets are on
- ✅ **All sensors** - Voltage, current, etc.

## Example Configuration

**Demo PDU on cloud server:**

```yaml
# Add via UI with these settings:
IP Address: 192.168.1.100
SNMP Community: demo
Device Name: Cloud Test PDU
Demo Mode: ✅ Enabled
```

**Multiple Demo PDUs:**

You can add multiple demo PDUs for testing:
- Demo PDU 1: `192.168.1.101`
- Demo PDU 2: `192.168.1.102`
- etc.

Each will have a unique serial number and work independently.

## Testing Scenarios

### Test 1: Basic Control
```yaml
# Turn on demo outlet 1
service: switch.turn_on
target:
  entity_id: switch.apc_pdu_outlet_1

# Check the power sensor
sensor.apc_pdu_outlet_1_power  # Should show ~145W
```

### Test 2: Power Monitoring
```yaml
# Turn on all outlets
service: switch.turn_on
target:
  entity_id: switch.apc_pdu_master_switch

# Check total power
# switch.apc_pdu_master_switch attribute 'total_power_w'
# Should show ~700W total
```

### Test 3: Load State
```yaml
# Turn on 1-2 outlets: "Normal"
# Turn on 6-7 outlets: "Near Overload"  
# Turn on 8 outlets: "High Load"
```

### Test 4: Automation Testing
```yaml
automation:
  - alias: "Demo High Power Alert"
    trigger:
      platform: numeric_state
      entity_id: switch.apc_pdu_master_switch
      attribute: total_power_w
      above: 500
    action:
      service: notify.notify
      data:
        message: "Demo PDU high power!"
```

## Demo Mode vs Real PDU

| Feature | Demo Mode | Real PDU |
|---------|-----------|----------|
| **Setup** | Instant | Requires SNMP config |
| **Network** | Not needed | Must be reachable |
| **Control** | Simulated | Actual hardware |
| **Power Values** | Simulated with variation | Real measurements |
| **Outlet Names** | Pre-defined | From PDU config |
| **Speed** | Instant response | SNMP network delay |
| **Reliability** | Always available | Network dependent |

## Switching from Demo to Real

When you're ready to use a real PDU:

1. **Remove Demo Entry**:
   - Settings → Devices & Services
   - Find your demo PDU
   - Click **⋮** → **Delete**

2. **Add Real PDU**:
   - Click **+ Add Integration**
   - Search "APC PDU"
   - Enter real IP and community
   - **DON'T** check Demo Mode
   - Submit

3. **Update Automations**:
   - Entity IDs will be the same
   - Automations should work unchanged

## Development Use

### Testing Features

Demo mode is perfect for:
- Testing new automations
- Creating dashboards
- Learning Home Assistant
- Developing scripts
- Writing documentation
- Recording tutorials

### Example: Dashboard Development

```yaml
# Test dashboard without hardware
type: vertical-stack
cards:
  - type: entities
    title: Demo PDU Control
    entities:
      - switch.apc_pdu_outlet_1
      - switch.apc_pdu_outlet_2
      - switch.apc_pdu_master_switch
  
  - type: history-graph
    title: Demo Power Usage
    hours_to_show: 24
    entities:
      - sensor.apc_pdu_outlet_1_power
      - sensor.apc_pdu_outlet_2_power
```

## Limitations

Demo mode has some limitations:
- ❌ No actual hardware control
- ❌ Power values are simulated (not real)
- ❌ No network latency simulation
- ❌ Outlet names are fixed (can't change via PDU)
- ❌ No SNMP errors to handle

But it's perfect for:
- ✅ Learning the integration
- ✅ Testing automations
- ✅ Cloud server testing
- ✅ Development

## Tips

1. **Use realistic IPs**: Even though they're fake, use realistic IPs to avoid confusion
2. **Name your demo PDUs**: Add "Demo" or "Test" in the name
3. **Test automations**: Perfect for testing before deploying to real hardware
4. **Multiple PDUs**: Test multi-PDU setups easily
5. **Power calculations**: Demo power values are consistent and useful for testing

## FAQ

**Q: Can I mix demo and real PDUs?**
A: Yes! You can have both demo and real PDUs in the same Home Assistant instance.

**Q: Will demo mode affect real PDUs?**
A: No, demo mode is completely separate. Each integration entry is independent.

**Q: Can I customize demo outlet names?**
A: Currently no, but you can rename entities in Home Assistant.

**Q: Do demo outlets remember their state?**
A: Yes, during the current session. State is lost on restart (like real PDUs without persistence).

**Q: Is demo mode slower than real PDU?**
A: No, it's actually faster since there's no SNMP network delay!

## Example: Complete Test Setup

```yaml
# 1. Add demo PDU
#    IP: 192.168.1.100
#    Community: demo
#    Demo Mode: ✅

# 2. Create test automation
automation:
  - alias: "Demo Test - Staggered Startup"
    trigger:
      platform: state
      entity_id: input_boolean.test_startup
      to: "on"
    action:
      - service: switch.turn_on
        target:
          entity_id: switch.apc_pdu_outlet_1
      - delay: "00:00:05"
      - service: switch.turn_on
        target:
          entity_id: switch.apc_pdu_outlet_2
      - delay: "00:00:05"
      - service: switch.turn_on
        target:
          entity_id: switch.apc_pdu_outlet_3

# 3. Create test dashboard
# 4. Test power monitoring
# 5. Verify everything works
# 6. Deploy to real PDU!
```

---

**Demo mode makes it easy to test and develop without needing physical hardware! 🎉**

