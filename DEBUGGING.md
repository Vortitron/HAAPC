# Debugging the APC PDU Integration

## Enhanced Logging (v1.0.0+)

The integration now has extensive logging to help diagnose connection issues.

## How to View Logs

### Option 1: Home Assistant UI (Easiest)

1. Go to **Settings** → **System** → **Logs**
2. Try adding your PDU
3. Look for entries starting with `custom_components.apc_pdu`

### Option 2: Command Line

```bash
# For Home Assistant OS
docker logs homeassistant -f | grep apc_pdu

# For Home Assistant Core
tail -f /config/home-assistant.log | grep apc_pdu
```

### Option 3: Set Debug Logging (Most Detailed)

Add to your `configuration.yaml`:

```yaml
logger:
  default: warning
  logs:
    custom_components.apc_pdu: debug
    custom_components.apc_pdu.config_flow: debug
    custom_components.apc_pdu.snmp_client: debug
```

Then restart Home Assistant.

## What the Logs Show

### Connection Attempt

When you try to add a PDU, you'll see:

```
WARNING (MainThread) [custom_components.apc_pdu.config_flow] === APC PDU Connection Attempt === Host: 192.168.1.28, Community: 5st***, Version: 1, Demo: False
```

This shows:
- ✅ Host IP address
- ✅ Community string (partially hidden for security)
- ✅ SNMP version
- ✅ Whether demo mode is enabled

### Client Selection

You'll see which SNMP method is being used:

```
WARNING (MainThread) [custom_components.apc_pdu.config_flow] Attempting to use pysnmp library...
WARNING (MainThread) [custom_components.apc_pdu.snmp_client] SNMPClient initialized: host=192.168.1.28, version=1 (mpModel=0), port=161
WARNING (MainThread) [custom_components.apc_pdu.config_flow] ✅ Successfully initialized pysnmp client
```

OR if pysnmp fails:

```
WARNING (MainThread) [custom_components.apc_pdu.config_flow] ⚠️ pysnmp not available (No module named 'pysnmp'), using command-line SNMP tools as fallback
WARNING (MainThread) [custom_components.apc_pdu.config_flow] ✅ Successfully initialized CLI SNMP client
```

### SNMP Operations

For each SNMP query, you'll see:

```
INFO (MainThread) [custom_components.apc_pdu.snmp_client] SNMP GET: .1.3.6.1.4.1.318.1.1.12.1.1.0 from 192.168.1.28 (community: 5s***, version: 0)
INFO (MainThread) [custom_components.apc_pdu.snmp_client] SNMP GET result for .1.3.6.1.4.1.318.1.1.12.1.1.0: MyPDU (type: str)
```

### Device Information

When device info is retrieved:

```
WARNING (MainThread) [custom_components.apc_pdu.snmp_client] Getting device info from 192.168.1.28...
WARNING (MainThread) [custom_components.apc_pdu.snmp_client] Device info result: {'name': 'MyPDU', 'model': 'AP7920', 'serial_number': 'ABC123', ...}
WARNING (MainThread) [custom_components.apc_pdu.config_flow] Device info retrieved: {'name': 'MyPDU', 'model': 'AP7920', ...}
WARNING (MainThread) [custom_components.apc_pdu.config_flow] ✅ Connection successful! Title: AP7920
```

### Errors

If something fails, you'll see detailed error information:

```
ERROR (MainThread) [custom_components.apc_pdu.snmp_client] SNMP error indication for OID .1.3.6.1.4.1.318.1.1.12.1.2.0: No SNMP response received before timeout
```

OR:

```
ERROR (MainThread) [custom_components.apc_pdu.config_flow] ❌ Failed to get device info: timeout (type: TimeoutError)
```

## Common Issues and Solutions

### Issue: "Failed to connect to PDU"

**Check the logs for:**

1. **Network timeout:**
   ```
   SNMP error indication: Request timed out
   ```
   **Solution:** Check network connectivity, firewall, PDU is powered on

2. **Wrong community string:**
   ```
   SNMP error indication: No SNMP response received
   ```
   **Solution:** Verify community string is correct

3. **Wrong SNMP version:**
   ```
   SNMP error status: noSuchObject
   ```
   **Solution:** Try version 2c instead of version 1

4. **pysnmp not available:**
   ```
   ⚠️ pysnmp not available (...), using command-line SNMP tools as fallback
   ```
   **Solution:** This is OK! CLI fallback will be used automatically

5. **Model field missing:**
   ```
   ❌ Device info missing 'model' field. Got: {'name': None, 'model': None, ...}
   ```
   **Solution:** PDU might not be an APC or uses different OIDs

### Issue: pysnmp Import Errors

If you see:
```
ERROR (MainThread) [custom_components.apc_pdu.snmp_client] pysnmp import failed: No module named 'pysnmp'
```

This means Home Assistant Core doesn't have pysnmp installed yet. Solutions:
1. **Use Demo Mode** for testing
2. **Install CLI tools** (HA Core only): `sudo apt-get install snmp`
3. **Wait for HA update** that includes pysnmp

## Testing with Demo Mode

To test the integration without a real PDU:

1. Add integration
2. Use any IP (e.g., `192.168.1.1`)
3. Use any community string (e.g., `test`)
4. **Enable "Demo Mode (for testing without hardware)"**
5. Submit

You should see:
```
WARNING (MainThread) [custom_components.apc_pdu.config_flow] Using Demo Mode (simulated PDU)
```

## Testing with Real PDU

1. Ensure PDU is on network and accessible
2. Try SNMP version 1 first (AP7920 default)
3. Use correct community string (default is often `private`)
4. **Disable** Demo Mode
5. Check logs for detailed connection attempt

## Reporting Issues

When reporting issues, please include:

1. **Log output** from the connection attempt (from WARNING and ERROR messages)
2. **PDU model** (e.g., AP7920, AP7921, etc.)
3. **Home Assistant version**
4. **Installation type** (HA OS, Container, Core)
5. **Whether pysnmp or CLI fallback is being used** (from logs)

## Example: Successful Connection

```
2025-10-10 10:00:00 WARNING (MainThread) [custom_components.apc_pdu.config_flow] === APC PDU Connection Attempt === Host: 192.168.1.28, Community: pri***, Version: 1, Demo: False
2025-10-10 10:00:00 WARNING (MainThread) [custom_components.apc_pdu.config_flow] Attempting to use pysnmp library...
2025-10-10 10:00:00 WARNING (MainThread) [custom_components.apc_pdu.snmp_client] SNMPClient initialized: host=192.168.1.28, version=1 (mpModel=0), port=161
2025-10-10 10:00:00 WARNING (MainThread) [custom_components.apc_pdu.config_flow] ✅ Successfully initialized pysnmp client
2025-10-10 10:00:00 WARNING (MainThread) [custom_components.apc_pdu.config_flow] Testing connection by retrieving device info...
2025-10-10 10:00:00 WARNING (MainThread) [custom_components.apc_pdu.snmp_client] Getting device info from 192.168.1.28...
2025-10-10 10:00:00 INFO (MainThread) [custom_components.apc_pdu.snmp_client] SNMP GET: .1.3.6.1.4.1.318.1.1.12.1.1.0 from 192.168.1.28 (community: pr***, version: 0)
2025-10-10 10:00:00 INFO (MainThread) [custom_components.apc_pdu.snmp_client] SNMP GET result for .1.3.6.1.4.1.318.1.1.12.1.1.0: MyPDU (type: str)
2025-10-10 10:00:01 INFO (MainThread) [custom_components.apc_pdu.snmp_client] SNMP GET result for .1.3.6.1.4.1.318.1.1.12.1.2.0: AP7920 (type: str)
2025-10-10 10:00:01 WARNING (MainThread) [custom_components.apc_pdu.snmp_client] Device info result: {'name': 'MyPDU', 'model': 'AP7920', 'serial_number': 'ABC123', ...}
2025-10-10 10:00:01 WARNING (MainThread) [custom_components.apc_pdu.config_flow] Device info retrieved: {'name': 'MyPDU', 'model': 'AP7920', ...}
2025-10-10 10:00:01 WARNING (MainThread) [custom_components.apc_pdu.config_flow] ✅ Connection successful! Title: AP7920
```

---

**The enhanced logging will help us identify exactly where and why the connection is failing!**

