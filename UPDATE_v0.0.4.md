# Update v0.0.4 - Demo Mode with Real SNMP Testing

## Overview

Demo Mode now **tries real SNMP first** before falling back to simulated data. This allows you to test SNMP connectivity on a cloud server or test system before deploying to production.

## What Changed

### Demo Mode Now Supports Real SNMP Testing

**Previously:** Demo Mode only returned simulated data.

**Now:** Demo Mode attempts real SNMP communication and falls back to simulated data if it fails.

This means you can:
1. ✅ **Test SNMP on your cloud server** - See if pysnmp is working even without the PDU
2. ✅ **Test real PDU connection** - Demo Mode will use real data if PDU is accessible
3. ✅ **Safe fallback** - Always works with simulated data if real SNMP fails
4. ✅ **Control real outlets** - In Demo Mode you can still control real PDU outlets

## How It Works

When you enable Demo Mode, the integration now:

1. **Tries to initialize real pysnmp client**
   - If pysnmp is available, creates a real SNMP client
   - If pysnmp is broken, logs warning and uses pure simulation

2. **For each operation (get device info, get outlet status, set outlet):**
   - First tries the real SNMP operation
   - If it succeeds, uses the real data
   - If it fails (timeout, wrong credentials, no PDU), falls back to simulated data

3. **Logs everything clearly:**
   ```
   WARNING Demo Mode: Attempting to use real SNMP first...
   WARNING ✅ Demo Mode: Real SNMP client available, will try real PDU first
   WARNING Demo Mode: Trying real SNMP for device info...
   WARNING ✅ Demo Mode: Got real device info: {'model': 'AP7920', ...}
   ```
   
   OR if real SNMP fails:
   ```
   WARNING ⚠️ Demo Mode: Real SNMP failed (timeout), using simulation
   INFO Demo Mode: Using simulated device info
   ```

## Use Cases

### Use Case 1: Testing on Cloud Server

You want to know if pysnmp will work before deploying to your home server:

1. Enable Demo Mode on your cloud HA instance
2. Enter your home PDU's IP and credentials (even though it's not accessible)
3. Check the logs:
   - If you see "Real SNMP client available" → pysnmp is working!
   - If you see "pysnmp not available" → you'll need to fix it or use CLI tools

### Use Case 2: Testing with Real PDU

You want to test controlling your real PDU but in a safe "Demo Mode" first:

1. Enable Demo Mode
2. Enter real PDU IP and credentials
3. The integration will:
   - Try to connect to real PDU
   - If successful, show "Got real device info" with your actual model
   - Allow you to control real outlets
   - Device name shows "(Demo Mode)" suffix so you know it's in demo

### Use Case 3: Pure Simulation

You just want to test the UI without any real hardware:

1. Enable Demo Mode
2. Enter any IP (e.g., 192.168.1.1)
3. pysnmp will fail (no PDU there)
4. Integration falls back to simulation
5. You get a fully working simulated PDU

## Example Logs

### Successful Real SNMP in Demo Mode:

```
2025-10-10 14:00:00 WARNING [custom_components.apc_pdu.config_flow] === APC PDU Connection Attempt === Host: 192.168.1.28, Community: 5st***, Version: 1, Demo: True
2025-10-10 14:00:00 WARNING [custom_components.apc_pdu.demo_client] Demo Mode: Attempting to use real SNMP first...
2025-10-10 14:00:00 WARNING [custom_components.apc_pdu.snmp_client] SNMPClient initialized: host=192.168.1.28, version=1 (mpModel=0), port=161
2025-10-10 14:00:00 WARNING [custom_components.apc_pdu.demo_client] ✅ Demo Mode: Real SNMP client available, will try real PDU first
2025-10-10 14:00:00 WARNING [custom_components.apc_pdu.demo_client] Demo SNMP client initialized for 192.168.1.28 (real_snmp=True)
2025-10-10 14:00:00 WARNING [custom_components.apc_pdu.config_flow] Testing connection by retrieving device info...
2025-10-10 14:00:00 WARNING [custom_components.apc_pdu.demo_client] Demo Mode: Trying real SNMP for device info...
2025-10-10 14:00:01 INFO [custom_components.apc_pdu.snmp_client] SNMP GET result for .1.3.6.1.4.1.318.1.1.12.1.5.0: AP7920 (type: str)
2025-10-10 14:00:01 WARNING [custom_components.apc_pdu.demo_client] ✅ Demo Mode: Got real device info: {'model': 'AP7920', ...}
2025-10-10 14:00:01 WARNING [custom_components.apc_pdu.config_flow] Device info retrieved: {'model': 'AP7920 (Demo Mode)', ...}
2025-10-10 14:00:01 WARNING [custom_components.apc_pdu.config_flow] ✅ Connection successful! Title: AP7920 (Demo Mode)
```

### pysnmp Broken, Using Pure Simulation:

```
2025-10-10 14:00:00 WARNING [custom_components.apc_pdu.demo_client] Demo Mode: Attempting to use real SNMP first...
2025-10-10 14:00:00 ERROR [custom_components.apc_pdu.snmp_client] pysnmp import failed: No module named 'pyasn1.compat.octets'
2025-10-10 14:00:00 WARNING [custom_components.apc_pdu.demo_client] ⚠️ Demo Mode: Cannot use real SNMP (pysnmp is not available...), using pure simulation
2025-10-10 14:00:00 WARNING [custom_components.apc_pdu.demo_client] Demo SNMP client initialized for 192.168.1.28 (real_snmp=True)
2025-10-10 14:00:00 INFO [custom_components.apc_pdu.demo_client] Demo Mode: Using simulated device info
2025-10-10 14:00:00 WARNING [custom_components.apc_pdu.config_flow] Device info retrieved: {'model': 'AP7920 (Demo)', ...}
2025-10-10 14:00:00 WARNING [custom_components.apc_pdu.config_flow] ✅ Connection successful! Title: AP7920 (Demo)
```

## Benefits

1. **Test Before Deploy** - Know if SNMP will work before copying to production
2. **Safe Testing** - Can test with real PDU in "Demo Mode" safety
3. **Debugging** - See exactly where SNMP fails (pysnmp broken vs network issue)
4. **Always Works** - Demo Mode never fails, always has fallback data
5. **Realistic Testing** - Can test with real PDU data while in demo mode

## Technical Details

- Demo Mode tries to import `SNMPClient` and check `SNMP_AVAILABLE`
- If available, creates real SNMP client alongside simulated client
- Each operation tries real SNMP first with try/except
- Failures are logged but don't break the integration
- Simulated data is always available as fallback

## Upgrading

Simply update the integration files and restart Home Assistant. Demo Mode will automatically try real SNMP.

---

**Released**: October 10, 2025
**Version**: 0.0.4

