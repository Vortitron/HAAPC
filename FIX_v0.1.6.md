# Quick Fix v0.1.6 - Async Factory Pattern

## 🔧 The Issue

The async API uses a **factory pattern** for constructing `UdpTransportTarget`:

**Error:**
```
Please call .create() to construct UdpTransportTarget object
```

## ✅ The Fix

Changed from direct instantiation to async factory method:

### ❌ Old (v0.1.5):
```python
target = UdpTransportTarget((self.host, self.port))
```

### ✅ New (v0.1.6):
```python
target = await UdpTransportTarget.create((self.host, self.port))
```

This is a common async pattern where the constructor can't be async, so a static `create()` method is used instead.

## 📁 Files Changed

- `custom_components/apc_pdu/snmp_client.py` - Use `.create()` factory method
- `custom_components/apc_pdu/manifest.json` - Version 0.1.6

## 🚀 This Should Work Now!

The async API pattern:
```python
async def _snmp_get_async(self, oid: str) -> Any:
    # Use async factory method
    target = await UdpTransportTarget.create((self.host, self.port))
    target.timeout = 5
    target.retries = 2
    
    result = await get_cmd(...)
```

Test it! 🎯

