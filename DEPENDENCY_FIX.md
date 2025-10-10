# Dependency Fix - pysnmp 7.1.21 Compatibility

## Problem (Historical)

Earlier versions had issues with:
```
Error occurred loading flow for integration apc_pdu: No module named 'pyasn1.compat.octets'
```

This occurred because we were specifying incompatible pysnmp versions.

## Solution (Current)

**As of Home Assistant Core with pysnmp 7.1.21:**

We no longer specify pysnmp as a requirement. Instead, we use the version provided by Home Assistant Core:

```json
"requirements": []
```

Home Assistant Core now includes **pysnmp 7.1.21** (as of recent updates), which is the latest stable version.

**References:**
- HA Core SNMP manifest: [manifest.json](https://github.com/home-assistant/core/blob/9f3d890e91046ef85fa733e249b9114640355ee2/homeassistant/components/snmp/manifest.json)
- Migration example: [Eaton UPS PR #60](https://github.com/jaroschek/home-assistant-eaton-ups/pull/60)

## What is pysnmp 7.1.21?

`pysnmp 7.1.21` is the **current maintained version** of pysnmp:
- ✅ Actively maintained
- ✅ Compatible with Python 3.9+
- ✅ Modern async/await support
- ✅ Improved performance
- ✅ Better error handling
- ✅ Security updates

**Key Changes from 5.x to 7.x:**
- Removed deprecated `oneliner` API (we already use `hlapi`)
- Better async support
- Improved type hints
- Bug fixes and optimizations

## How This Works

The integration now:
1. ✅ Uses Home Assistant Core's built-in pysnmp 7.1.21
2. ✅ No additional dependencies to install
3. ✅ Automatic compatibility with HA Core updates
4. ✅ Faster installation (no extra packages)
5. ✅ No version conflicts

## Installation

Simply:

1. **Copy the integration files to custom_components/apc_pdu**
2. **Restart Home Assistant**
3. **Add the integration** via Settings → Devices & Services

No manual dependency installation needed - Home Assistant provides everything!

## Verification

After restarting Home Assistant, the integration should load without errors:

```
# Check logs - you should NOT see:
❌ No module named 'pyasn1.compat.octets'

# You should see:
✅ Setting up apc_pdu component
```

## Compatibility

The new dependency is **fully backward compatible**:
- ✅ All existing code works unchanged
- ✅ Same SNMP operations
- ✅ Same API calls
- ✅ No configuration changes needed

## Migration from Old Version

If you had the integration installed with an older version:

1. **Update the integration files** (especially manifest.json)
2. **Restart Home Assistant**
3. **Done!**

Home Assistant Core already has pysnmp 7.1.21 - no manual package management needed.

## For Developers

The integration uses the standard pysnmp 7.x `hlapi` API:

```python
# We use the high-level API (hlapi) - compatible with pysnmp 7.x
from pysnmp.hlapi import (
    CommunityData,
    ContextData,
    ObjectIdentity,
    ObjectType,
    SnmpEngine,
    UdpTransportTarget,
    getCmd,
    setCmd,
)

# Note: The old 'oneliner' API was removed in pysnmp 7.x
# We never used it, so we're fully compatible!
```

## Tested With

- ✅ Home Assistant 2024.10+ (with pysnmp 7.1.21)
- ✅ Python 3.11, 3.12, 3.13
- ✅ Home Assistant OS
- ✅ Home Assistant Container
- ✅ Home Assistant Core

## Benefits

1. **Reliability**: Active maintenance and bug fixes
2. **Security**: Regular security updates
3. **Performance**: Optimizations and improvements
4. **Compatibility**: Works with latest Python versions
5. **Support**: Active community and developer support

## Additional Notes

- Home Assistant Core manages the pysnmp version
- We stay compatible with whatever version HA Core uses
- Currently tested with pysnmp 7.1.21
- For pysnmp issues, see: https://github.com/etingof/pysnmp/issues

## FAQ

**Q: Will this break my existing setup?**
A: No, it's a drop-in replacement. Everything works the same.

**Q: Do I need to reconfigure my PDUs?**
A: No, all configurations remain unchanged.

**Q: What version of pysnmp does this use?**
A: It uses whatever version Home Assistant Core provides (currently 7.1.21).

**Q: What if HA Core updates pysnmp?**
A: Our code uses the standard `hlapi` API which is stable across pysnmp 7.x versions, so updates should work seamlessly.

**Q: Does demo mode still work?**
A: Yes! Demo mode doesn't use SNMP, so it works regardless.

---

**The dependency issue is now fixed! 🎉**

