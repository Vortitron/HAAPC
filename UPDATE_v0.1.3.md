# Update v0.1.3 - Fixed pysnmp Import Path!

## 🎯 The Discovery

By analyzing [Home Assistant's SNMP integration source code](https://github.com/home-assistant/core/tree/dev/homeassistant/components/snmp), we found the key difference:

### ❌ What We Were Using (WRONG):
```python
from pysnmp.hlapi import (
    CommunityData, SnmpEngine, etc.
)
```

### ✅ What Home Assistant Uses (CORRECT):
```python
from pysnmp.hlapi.v3arch.asyncio import (
    CommunityData, SnmpEngine, etc.
)
```

### ✅ What We Now Use (CORRECT):
```python
from pysnmp.hlapi.v3arch.sync import (
    CommunityData, SnmpEngine, etc.
)
```

## 🔍 The Analysis

From [HA's SNMP sensor.py](https://github.com/home-assistant/core/blob/dev/homeassistant/components/snmp/sensor.py):

```python
from pyasn1.codec.ber import decoder
from pysnmp.error import PySnmpError
import pysnmp.hlapi.v3arch.asyncio as hlapi
from pysnmp.hlapi.v3arch.asyncio import (
    CommunityData,
    Udp6TransportTarget,
    UdpTransportTarget,
    UsmUserData,
    get_cmd,
)
```

**Key Points:**
1. HA uses the `v3arch` architecture (version 3 architecture)
2. HA uses the `asyncio` variant (async methods)
3. We need the `sync` variant (sync methods, since we run in executors)

## 🔧 What Changed

### Updated File
- `custom_components/apc_pdu/snmp_client.py`
  - Primary import: `pysnmp.hlapi.v3arch.sync`
  - Fallback import: `pysnmp.hlapi` (old path)
  - Logs which import path succeeded

### Version
- `custom_components/apc_pdu/manifest.json` - Version 0.1.3

### Documentation
- `CHANGELOG.md` - Added v0.1.3 notes

## 🚀 What This Means

Since your YAML SNMP config works, HA successfully imports from `pysnmp.hlapi.v3arch`. Now our integration uses the **same module structure**, so it should work too!

### The Import Strategy
```python
try:
    # Try v3arch.sync (same architecture as HA, but sync version)
    from pysnmp.hlapi.v3arch.sync import ...
    _IMPORT_SOURCE = "pysnmp.hlapi.v3arch.sync"
except ImportError:
    try:
        # Fallback to old path
        from pysnmp.hlapi import ...
        _IMPORT_SOURCE = "pysnmp.hlapi"
    except ImportError:
        # Neither worked
        SNMP_AVAILABLE = False
```

## 🧪 Testing

### Expected Logs (Demo Mode - Success):

```
INFO Successfully imported pysnmp from: pysnmp.hlapi.v3arch.sync
WARNING Demo Mode: Attempting to use real SNMP first...
✅ Demo Mode: Real SNMP client available, will try real PDU first
```

### Expected Logs (Demo Mode - Fallback):

```
INFO Successfully imported pysnmp from: pysnmp.hlapi
WARNING Demo Mode: Attempting to use real SNMP first...
✅ Demo Mode: Real SNMP client available, will try real PDU first
```

### Expected Logs (Demo Mode - Still Failing):

```
ERROR Failed to import pysnmp: v3arch.sync: [...], hlapi: [...]
WARNING Demo Mode: Attempting to use real SNMP first...
⚠️ Demo Mode: pysnmp not available, using pure simulation
```

## 📊 Why This Should Work

Looking at HA's source code structure:

1. **HA's SNMP integration** successfully imports `pysnmp.hlapi.v3arch.asyncio`
2. **Your YAML SNMP** sensors work, proving HA's pysnmp is functional
3. **Our integration** now uses `pysnmp.hlapi.v3arch.sync` (same `v3arch` structure)
4. **Result**: If HA's v3arch works, ours should too!

## 🔗 References

- [HA SNMP Integration Docs](https://www.home-assistant.io/integrations/snmp/)
- [HA SNMP sensor.py Source](https://github.com/home-assistant/core/blob/dev/homeassistant/components/snmp/sensor.py)
- [HA SNMP util.py Source](https://github.com/home-assistant/core/blob/dev/homeassistant/components/snmp/util.py)
- [HA SNMP switch.py Source](https://github.com/home-assistant/core/blob/dev/homeassistant/components/snmp/switch.py)

## 🎉 Next Steps

1. **Copy updated files** to your HA server
2. **Restart Home Assistant**
3. **Add integration with Demo Mode**
4. **Check logs** for the import source message
5. **Report back** what you see!

The logs will now explicitly tell us:
- ✅ Which import path succeeded
- ✅ Whether SNMP is available
- ✅ Whether Demo Mode can use real SNMP

This is the most targeted fix yet - we're now using the exact same pysnmp module architecture as Home Assistant's own SNMP integration! 🚀

