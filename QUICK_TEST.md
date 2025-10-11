# ⚡ Quick Test on Real PDU - v1.0.0

## 🚀 5-Minute Test Procedure

### Step 1: Copy Files (1 min)
```bash
# Copy to your Home Assistant server
scp -r custom_components/apc_pdu /config/custom_components/
```

### Step 2: Restart HA (2 min)
- Settings → System → Restart
- Wait for restart to complete

### Step 3: Add Integration (1 min)
- Settings → Devices & Services → **+ ADD INTEGRATION**
- Search: **"APC PDU"**
- Fill in:
  - **IP**: `192.168.1.28`
  - **Community**: `5stream`
  - **Version**: `1`
  - **Demo Mode**: ❌ **OFF**
- Click **SUBMIT**

### Step 4: Check Result (1 min)
**✅ SUCCESS if you see:**
- Device "AP7920" appears
- 8 outlet switches
- All entities available
- No errors in logs

**❌ FAILED if you see:**
- "Failed to connect" error
- Device added but entities unavailable
- Timeout errors in logs

## 🔍 Quick Diagnostics

### Check Logs
Settings → System → Logs → Filter: "apc_pdu"

**Look for:**
```
✅ Successfully imported pysnmp from: pysnmp.hlapi.v3arch.asyncio
✅ SNMPClient initialized: host=192.168.1.28
✅ SNMP GET (async) result for .1.3.6.1.4.1.318.1.1.12.1.5.0: AP7920
```

### Test Connectivity
From HA Terminal/SSH:
```bash
ping 192.168.1.28
nc -zv 192.168.1.28 161
```

## 📊 Expected Entities

After successful setup, you should have:

**Switches:**
- `switch.ap7920_outlet_1` through `8`
- `switch.ap7920_master_switch`

**Sensors:**
- `sensor.ap7920_outlet_1_power` through `8` (if supported)
- `sensor.ap7920_rated_voltage`
- `sensor.ap7920_rated_max_current`
- `sensor.ap7920_bank_load_state`
- `sensor.ap7920_outlet_count`
- `sensor.ap7920_hardware_version`
- `sensor.ap7920_firmware_version`

## 🎯 Quick Test

**Test 1: Toggle Outlet**
1. Click on `switch.ap7920_outlet_1`
2. Toggle it
3. Check if physical outlet turns on/off
4. ✅ Pass if it works

**Test 2: Master Switch**
1. Click on `switch.ap7920_master_switch`
2. Turn it ON
3. Check if ALL outlets turn on
4. ✅ Pass if it works

**Test 3: Power Monitoring**
1. Check `sensor.ap7920_outlet_1_power`
2. Should show Watts
3. ✅ Pass if shows number (not "unavailable")

## 🐛 Common Issues & Fixes

### "Failed to connect"
- ✅ Check IP is correct
- ✅ Check community string (case-sensitive!)
- ✅ Verify PDU is powered on
- ✅ Test with ping/nc commands

### Entities "unavailable"
- ✅ Check logs for SNMP errors
- ✅ Verify SNMP enabled on PDU
- ✅ Try restarting HA
- ✅ Check community is read-write

### "Demo Mode" in name
- ✅ Demo Mode was enabled
- ✅ Delete device and re-add
- ✅ Make sure Demo Mode checkbox is OFF

## 📝 Report Back

Tell me:
- ✅ What worked
- ❌ What failed
- 📋 Any error messages
- 💡 Ideas for improvements

## 🎉 If It Works

**Congratulations!** You now have:
- ✅ Full PDU control from Home Assistant
- ✅ All outlets in one device
- ✅ Easy automation setup
- ✅ Power monitoring (if supported)
- ✅ Professional integration

**Next:**
- Remove old YAML config
- Update automations
- Update dashboards
- Test automations
- Enjoy! 🚀

---

**Version**: 1.0.0  
**Status**: Production Ready  
**Tested**: Demo Mode ✅ | Real PDU ⏳

