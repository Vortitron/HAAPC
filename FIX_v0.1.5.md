# Quick Fix v0.1.5 - Async API Signature Correction

## 🎉 The Good News

**Version 0.1.4 worked!** The pysnmp import succeeded:
```
✅ Demo Mode: Real SNMP client available, will try real PDU first
```

## 🔧 The Issue Found

The async API has a **different UdpTransportTarget signature** than the sync API:

### ❌ What We Were Doing (Wrong):
```python
# Sync signature used with async API
UdpTransportTarget((self.host, self.port), timeout=5, retries=2)
```

**Error:**
```
AbstractTransportTarget.__init__() got multiple values for argument 'timeout'
```

### ✅ What We Should Do (Correct):
```python
# Async API signature
target = UdpTransportTarget((self.host, self.port))
target.timeout = 5
target.retries = 2
```

## 🔄 The Fix

Updated both async methods:

### _snmp_get_async():
```python
async def _snmp_get_async(self, oid: str) -> Any:
    try:
        # Async API uses different UdpTransportTarget signature
        target = UdpTransportTarget((self.host, self.port))
        target.timeout = 5
        target.retries = 2
        
        error_indication, error_status, error_index, var_binds = await get_cmd(
            SnmpEngine(),
            CommunityData(self.community, mpModel=self.version),
            target,
            ContextData(),
            ObjectType(ObjectIdentity(oid)),
        )
        # ... rest of code
```

### _snmp_set_async():
```python
async def _snmp_set_async(self, oid: str, value: int) -> bool:
    try:
        from pysnmp.proto.rfc1902 import Integer
        
        # Async API uses different UdpTransportTarget signature
        target = UdpTransportTarget((self.host, self.port))
        target.timeout = 5
        target.retries = 2
        
        error_indication, error_status, error_index, var_binds = await set_cmd(
            SnmpEngine(),
            CommunityData(self.community, mpModel=self.version),
            target,
            ContextData(),
            ObjectType(ObjectIdentity(oid), Integer(value)),
        )
        # ... rest of code
```

## 📁 Files Changed

- `custom_components/apc_pdu/snmp_client.py` - Fixed async method signatures
- `custom_components/apc_pdu/manifest.json` - Version 0.1.5
- `CHANGELOG.md` - Added v0.1.5 notes

## 🧪 Expected Result

Now you should see:
```
INFO ✅ Successfully imported pysnmp from: pysnmp.hlapi.v3arch.asyncio (async=True)
WARNING Demo Mode: Attempting to use real SNMP first...
✅ Demo Mode: Real SNMP client available, will try real PDU first
INFO Demo Mode: Trying real SNMP for device info...
INFO SNMP GET (async) result for .1.3.6.1.4.1.318.1.1.12.1.5.0: AP7920
✅ Demo Mode: Got real device info: {'model': 'AP7920', ...}
```

## 🚀 Testing

1. **Copy updated file** to HA server (just `snmp_client.py` and `manifest.json`)
2. **Restart HA**
3. **Try again** - should work now!

The pysnmp import is **confirmed working**, we just needed to fix the async API signature! 🎯

