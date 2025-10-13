# Logging Levels - APC PDU Integration

## Current Log Levels (v1.0.0)

The integration uses appropriate log levels to avoid spam while still providing useful information:

### INFO Level (Important Events)
- ✅ Successful pysnmp client initialization
- ✅ Successful CLI client initialization
- ✅ Connection successful during setup
- ✅ Demo Mode using real SNMP successfully
- ⚠️ Pysnmp not available (fallback to CLI)
- 🎯 Demo Mode enabled

### DEBUG Level (Normal Operations)
- SNMP GET operations
- SNMP GET results
- Device info retrieval
- Client initialization details
- Demo Mode operations

### ERROR Level (Problems)
- SNMP error indications (timeouts, failures)
- SNMP error status
- Failed device info retrieval
- Import errors

## Default Behaviour

**Normal Operation:** Quiet logs with only important events (INFO+)
- Setup: 1-2 INFO messages
- Runtime: No messages (all operations at DEBUG level)

**Enable Debug Logging:**
```yaml
# configuration.yaml
logger:
  default: info
  logs:
    custom_components.apc_pdu: debug
```

## What Changed in v1.0.0

**Reduced from WARNING to DEBUG:**
- All SNMP GET operations
- All device info retrievals
- Client initialization
- Connection attempts
- Demo Mode normal operations

**Kept as INFO:**
- Integration setup success/failure
- Client type selection
- Important state changes

**Kept as ERROR:**
- SNMP timeouts
- Connection failures
- Invalid responses

## Log Examples

### Normal Setup (INFO level)
```
INFO Successfully imported pysnmp from: pysnmp.hlapi.v3arch.asyncio (async=True)
INFO ✅ Successfully initialized pysnmp client
INFO ✅ Connection successful! Title: AP7920
```

### Runtime (DEBUG level required to see)
```
DEBUG SNMP GET: .1.3.6.1.4.1.318.1.1.12.1.5.0 from 192.168.1.28 (community: 5s***, version: 0)
DEBUG SNMP GET (async) result for .1.3.6.1.4.1.318.1.1.12.1.5.0: AP7920 (type: str)
DEBUG Getting device info from 192.168.1.28...
```

### Errors (Always shown)
```
ERROR SNMP error indication for OID .1.3.6.1.4.1.318.1.1.12.1.5.0: No SNMP response received before timeout
ERROR ❌ Failed to get device info: timeout (type: TimeoutError)
```

## Benefits

✅ **Quiet by default** - No log spam during normal operation
✅ **Debug when needed** - Full details available with debug logging
✅ **Errors always visible** - Problems are immediately apparent
✅ **Professional** - Follows Home Assistant logging best practices

