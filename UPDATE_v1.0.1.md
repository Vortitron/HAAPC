# Version 1.0.1 Update

## 🐛 Bug Fixes

### Fixed Syntax Error in snmp_client.py
**Issue**: Python syntax error on line 80 preventing integration from loading
```python
# ❌ OLD (incorrect nested ternary)
return int(value) if value.isdigit() if isinstance(value, str) else value

# ✅ FIXED
if isinstance(value, str) and value.isdigit():
    return int(value)
return value
```

**Impact**: Integration now loads properly in Home Assistant

---

## 🎮 New Feature: Demo Mode

### What is Demo Mode?
Test the integration **without physical PDU hardware**!

Perfect for:
- ✅ Cloud servers with no network access to PDU
- ✅ Development and testing
- ✅ Learning automations
- ✅ Creating dashboards before hardware arrival

### How to Enable
When adding the integration:
1. Settings → Devices & Services → Add Integration
2. Search "APC PDU"
3. Enter any IP/community (they won't be used)
4. **Check "Demo Mode"** ✅
5. Submit

### What You Get
- **Simulated AP7920 PDU** with 8 outlets
- **Realistic power monitoring** (145W, 180W, 45W, etc.)
- **Power variation** (±10% per update)
- **Working switches** (state persists during session)
- **Load state** changes based on usage
- **All sensors** work (voltage, current, etc.)

### Demo Outlet Names
1. Server 1 (~145W)
2. Server 2 (~180W)
3. Network Switch (~45W)
4. Router (~25W)
5. NAS (~90W)
6. Workstation (~120W)
7. Monitor (~60W)
8. Misc Device (~35W)

---

## 📦 Files Changed

### Modified Files
- `custom_components/apc_pdu/snmp_client.py` - Fixed syntax error
- `custom_components/apc_pdu/const.py` - Added CONF_DEMO_MODE
- `custom_components/apc_pdu/config_flow.py` - Added demo mode option
- `custom_components/apc_pdu/coordinator.py` - Support demo client
- `custom_components/apc_pdu/strings.json` - Added demo mode label
- `custom_components/apc_pdu/translations/en.json` - Added demo mode label
- `README.md` - Documented demo mode

### New Files
- `custom_components/apc_pdu/demo_client.py` - Demo SNMP client implementation
- `DEMO_MODE.md` - Complete demo mode documentation

---

## 🚀 Upgrade Instructions

### If Installed Manually
1. Copy new files to `/config/custom_components/apc_pdu/`
2. Restart Home Assistant
3. Existing PDUs continue working normally
4. Can now add demo PDUs if needed

### If Using HACS
1. HACS → Integrations → APC PDU → Update
2. Restart Home Assistant

---

## 🧪 Testing Demo Mode

### Quick Test
```yaml
# Add demo PDU
IP: 192.168.1.100 (can be anything)
Community: demo
Demo Mode: ✅ Enabled

# Then test:
service: switch.turn_on
target:
  entity_id: switch.apc_pdu_outlet_1

# Check power:
sensor.apc_pdu_outlet_1_power  # ~145W
```

### Create Test Automation
```yaml
automation:
  - alias: "Demo Test"
    trigger:
      platform: numeric_state
      entity_id: switch.apc_pdu_master_switch
      attribute: total_power_w
      above: 500
    action:
      service: notify.notify
      data:
        message: "Demo PDU power: {{ state_attr('switch.apc_pdu_master_switch', 'total_power_w') }}W"
```

---

## ✅ Compatibility

- ✅ **Backward Compatible**: Existing PDUs work unchanged
- ✅ **Mix Real and Demo**: Can have both types simultaneously
- ✅ **Same Features**: Demo mode supports all integration features
- ✅ **No Breaking Changes**: Entity IDs remain the same

---

## 📝 Notes

1. **Demo mode is optional** - unchecked by default
2. **Real PDUs unaffected** - demo mode only applies to new entries
3. **State persistence** - demo outlet states persist during HA session
4. **Unique serials** - each demo PDU gets unique serial (DEMO-IP-ADDRESS)
5. **No network required** - demo mode works completely offline

---

## 🔜 Future Enhancements

Planned for future releases:
- [ ] Configurable demo outlet names
- [ ] Adjustable demo power values
- [ ] Simulate SNMP delays
- [ ] Error simulation mode
- [ ] Custom outlet count

---

## 📚 Documentation

- **[DEMO_MODE.md](DEMO_MODE.md)** - Complete demo mode guide
- **[README.md](README.md)** - Updated with demo mode info
- **[QUICKSTART.md](QUICKSTART.md)** - Quick setup guide
- **[EXAMPLES.md](EXAMPLES.md)** - Automation examples

---

**Version 1.0.1 is ready! Test on your cloud server now! 🎉**

