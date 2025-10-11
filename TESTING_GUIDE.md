# Testing Guide - Version 1.0.0

## 🎯 What We've Achieved

✅ **SNMP Communication Working**
- Successfully imports `pysnmp.hlapi.v3arch.asyncio` (Home Assistant's exact path)
- Async API properly wrapped for sync execution
- Timeout handling works correctly
- Demo Mode falls back to simulation gracefully

## 📋 Testing on Real PDU

### Step 1: Prepare Files

From your development machine:
```bash
# Copy integration to your Home Assistant
scp -r custom_components/apc_pdu user@your-ha-server:/config/custom_components/
```

Or if using HA OS, copy via:
- Samba share
- File editor add-on
- Terminal & SSH add-on

### Step 2: Restart Home Assistant

- Settings → System → Restart
- Wait for HA to fully restart (check logs for "Home Assistant is running")

### Step 3: Add Integration

1. Go to **Settings → Devices & Services**
2. Click **+ ADD INTEGRATION**
3. Search for **"APC PDU"**
4. Fill in configuration:
   - **IP Address**: `192.168.1.28` (your PDU IP)
   - **SNMP Community**: `5stream` (your community string)
   - **Device Name**: (optional) `cAPC3` or leave blank
   - **SNMP Version**: `1` (or `2c` if your PDU uses v2c)
   - **Demo Mode**: ❌ **OFF** (for real PDU testing)

### Step 4: Check Logs

Go to **Settings → System → Logs** and look for:

**Expected SUCCESS logs:**
```
INFO Successfully imported pysnmp from: pysnmp.hlapi.v3arch.asyncio (async=True)
INFO Using pysnmp library for SNMP communication
WARNING SNMPClient initialized: host=192.168.1.28, version=1, port=161
INFO SNMP GET (async) result for .1.3.6.1.4.1.318.1.1.12.1.5.0: AP7920
WARNING Device info retrieved: {'model': 'AP7920', 'serial_number': '...', ...}
```

**If you see timeout errors:**
- Check PDU is powered on and accessible
- Verify IP address: `ping 192.168.1.28`
- Test SNMP manually if possible: `snmpget -v1 -c 5stream 192.168.1.28 .1.3.6.1.4.1.318.1.1.12.1.5.0`
- Confirm community string is correct
- Check firewall allows UDP port 161

### Step 5: Verify Device

1. **Device should appear** in Settings → Devices & Services → APC PDU
2. **Device info should show:**
   - Model: AP7920 (or your model)
   - Manufacturer: APC
   - Serial number
   - Firmware version
   - Hardware version

3. **Entities should be created:**
   - 8 outlet switches (or your outlet count)
   - 1 master switch
   - Power sensors (if your PDU supports it)
   - Status sensors

### Step 6: Test Functionality

**Test Outlet Control:**
1. Go to a switch entity (e.g., "Outlet 1")
2. Toggle it on/off
3. Verify:
   - Switch state changes in HA
   - Physical outlet turns on/off
   - Logs show SNMP SET commands

**Test Power Monitoring:**
1. Check power sensor entities
2. Values should update every 30 seconds
3. Should show current power draw in Watts

**Test Master Switch:**
1. Toggle master switch
2. Should control all outlets at once

## 🐛 Troubleshooting

### Issue: "Failed to connect to PDU"

**Check:**
- PDU IP address is correct and reachable
- SNMP is enabled on PDU
- Community string matches (case-sensitive!)
- SNMP version is correct (v1 vs v2c)

**Test manually:**
```bash
# From HA terminal or SSH
ping 192.168.1.28
nc -zv 192.168.1.28 161
```

### Issue: Device added but all entities "unavailable"

**Check logs for:**
- SNMP timeout errors → Network issue
- SNMP error responses → Wrong OIDs for your PDU model
- Import errors → pysnmp still broken (unlikely at this point!)

**Verify:**
- Check coordinator logs show successful updates
- Try restarting HA
- Check PDU web interface for SNMP settings

### Issue: "Demo Mode" appears in device name

**Solution:**
- Demo Mode was enabled during setup
- Delete device from HA
- Re-add with Demo Mode **disabled**

### Issue: Can read status but can't control outlets

**Check:**
- Community string must be **read-write** (not read-only)
- Usually "private" is read-write, "public" is read-only
- Verify in PDU SNMP settings

## ✅ Success Criteria

Integration is working correctly when:
- ✅ Device appears with correct model name
- ✅ All outlet switches are available
- ✅ Can toggle outlets on/off
- ✅ Master switch controls all outlets
- ✅ Power monitoring shows values (if supported)
- ✅ Status updates every 30 seconds
- ✅ No errors in logs

## 📊 Comparing with YAML Config

Your old YAML config (`ap7920/configuration.yaml`) should be replaced by this integration.

**YAML Entities** → **Integration Entities**
- `sensor.capc3_model_number` → Device info attribute
- `switch.capc3_outlet_1` → `switch.ap7920_outlet_1`
- Manual sensors → Automatic power sensors
- Individual entities → Grouped under one device

**Benefits:**
- ✅ All entities grouped under device
- ✅ Easy to add more PDUs
- ✅ UI configuration (no YAML editing)
- ✅ Automatic entity naming
- ✅ Better organization

## 🎉 Next Steps After Success

1. **Remove old YAML config** (if migrating)
2. **Update automations** to use new entity IDs
3. **Update dashboards** to use new device
4. **Test automations** to ensure they work
5. **Document your setup** for future reference
6. **Consider adding more PDUs** if you have them!

## 📝 Report Back

Please test and report:
- ✅ What worked
- ❌ What didn't work
- 📋 Any error messages
- 💡 Any suggestions for improvement

Good luck testing! 🚀

