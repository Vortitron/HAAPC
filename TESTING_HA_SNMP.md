# Testing SNMP Compatibility

## 🎯 Goal

Since Home Assistant's built-in SNMP platform works on your system, this integration should work too! We use the same pysnmp library that HA uses.

## 📋 What to Expect

### Version 0.1.2 - Direct pysnmp Usage

The integration uses standard pysnmp imports (same as HA's SNMP platform). When you add the integration:

**Without Demo Mode (Production):**
1. **Tries pysnmp library** (same as HA's SNMP platform uses)
2. **Falls back to CLI tools** if pysnmp import fails
3. **Connects to your real PDU** if network accessible

**With Demo Mode (Testing):**
1. **Tries pysnmp library** to see if it's available
2. **Falls back to pure simulation** if not available
3. **Never tries to connect to real PDU** (safe for testing)

The logs will tell you **exactly** which method is being used!

## 🧪 Testing Steps

### 1. Copy Files to Your HA Server

Copy the updated `custom_components/apc_pdu/` directory to your Home Assistant.

### 2. Restart Home Assistant

Full restart required to load the new code.

### 3. Add Integration with Demo Mode Enabled

- Go to Settings → Devices & Services
- Add Integration → "APC PDU"
- Fill in:
  - **IP Address**: Your PDU IP (doesn't need to be reachable in Demo Mode)
  - **SNMP Community**: Your community string
  - **SNMP Version**: v1 or v2c
  - ✅ **Enable Demo Mode**

### 4. Check the Logs

Go to Settings → System → Logs and look for:

#### ✅ Success - pysnmp Available:
```
WARNING Demo Mode: Attempting to use real SNMP first...
✅ Demo Mode: Real SNMP client available, will try real PDU first
```

#### ℹ️ Pure Simulation - No SNMP Available:
```
WARNING Demo Mode: Attempting to use real SNMP first...
⚠️ Demo Mode: HA SNMP not available (...), trying pysnmp...
⚠️ Demo Mode: pysnmp not available, using pure simulation
```

## 📊 Understanding the Results

### If pysnmp is Available ✅

**Great news!** When you deploy to your home server with the real PDU:
- Disable Demo Mode
- The integration will use pysnmp to communicate with your PDU
- Same library that HA's SNMP platform uses
- No dependency issues, no manual fixes needed!

### If Only pysnmp is Available ⚠️

The integration will work but may be subject to the pysnmp bugs in HA 2024.10.x. Consider:
- Using CLI fallback (if on HA Core)
- Waiting for HA to fix pysnmp
- Keep using Demo Mode for testing

### If Neither is Available ℹ️

You're likely on Home Assistant OS/Container without SNMP support. Options:
- Use Demo Mode for testing on cloud server
- Deploy to home server where PDU is accessible
- The integration will still work on your home server (it has 4 fallback methods!)

## 🎨 What Demo Mode Shows

Even in Demo Mode, you'll get a fully functional integration with:
- 8 simulated outlets with realistic names
- Power monitoring (simulated values)
- Master switch
- All the same entities as the real PDU

This lets you:
- ✅ Test automations and dashboards
- ✅ Verify the integration structure
- ✅ See which SNMP method would work
- ✅ Prepare for deployment to your home server

## 🚀 Next Steps

After testing on your cloud server:

1. **Copy to your home server** (where the PDU is accessible)
2. **Restart Home Assistant**
3. **Add integration WITHOUT Demo Mode**
4. **Enter real PDU IP and credentials**
5. **Check logs to see which method is used**

The integration will automatically select the best method and connect to your real PDU!

## 📝 Log Examples

### Full Success Log (pysnmp):
```
2025-10-10 15:00:00.123 WARNING [custom_components.apc_pdu.config_flow] === APC PDU Connection Attempt === Host: 192.168.1.28, Community: 5st***, Version: 1, Demo: True
2025-10-10 15:00:00.124 WARNING [custom_components.apc_pdu.config_flow] Using Demo Mode (simulated PDU)
2025-10-10 15:00:00.125 WARNING [custom_components.apc_pdu.demo_client] Demo Mode: Attempting to use real SNMP first...
2025-10-10 15:00:00.126 WARNING [custom_components.apc_pdu.demo_client] ✅ Demo Mode: Real SNMP client available, will try real PDU first
2025-10-10 15:00:00.127 WARNING [custom_components.apc_pdu.demo_client] Demo SNMP client initialized for 192.168.1.28 (real_snmp=True)
2025-10-10 15:00:00.128 WARNING [custom_components.apc_pdu.config_flow] Testing connection by retrieving device info...
2025-10-10 15:00:00.129 WARNING [custom_components.apc_pdu.demo_client] Demo Mode: Trying real SNMP for device info...
```

### Fallback to Simulation:
```
2025-10-10 15:00:00.123 WARNING [custom_components.apc_pdu.demo_client] Demo Mode: Attempting to use real SNMP first...
2025-10-10 15:00:00.124 WARNING [custom_components.apc_pdu.demo_client] ⚠️ Demo Mode: pysnmp not available, using pure simulation
2025-10-10 15:00:00.125 WARNING [custom_components.apc_pdu.demo_client] Demo SNMP client initialized for 192.168.1.28 (real_snmp=True)
2025-10-10 15:00:00.126 INFO    [custom_components.apc_pdu.demo_client] Demo Mode: Using simulated device info
```

## 💡 Tips

- **Always check the logs first** - they tell you exactly what's happening
- **Demo Mode is safe** - it never actually connects to the PDU
- **Test on cloud first** - see what SNMP methods are available before deploying
- **Document your results** - note which method worked for future reference

Good luck testing! The logs will guide you through everything. 🎉

