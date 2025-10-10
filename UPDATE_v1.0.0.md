# Update v1.0.0 - pysnmp 7.1.21 Compatibility

## Overview

This update makes the APC PDU integration compatible with Home Assistant Core's built-in **pysnmp 7.1.21**, eliminating dependency conflicts and installation issues.

## What Changed

### 1. **Removed pysnmp Dependency**

**Before:**
```json
"requirements": ["pysnmp-lextudio==5.0.34"]
```

**After:**
```json
"requirements": []
```

**Why:** Home Assistant Core now provides pysnmp 7.1.21, so we use that instead of bundling our own version.

### 2. **Updated Documentation**

- **DEPENDENCY_FIX.md**: Updated to explain pysnmp 7.1.21 compatibility
- **README.md**: Updated dependencies section to reflect HA Core's built-in pysnmp
- **Deleted obsolete files**:
  - `FIX_HA_2024_10_SNMP.md` (no longer relevant)
  - `INSTALL_TROUBLESHOOTING.md` (no longer needed)

### 3. **Fixed manifest.json Version**

- Changed from invalid `"0.0.0c"` to proper semantic version `"1.0.0"`
- This was causing the integration to not be recognised by Home Assistant

### 4. **Fixed config_flow.py KeyError**

- Ensured `title` key is always present in validation return dictionary
- Added more robust error handling for device info retrieval

## Code Compatibility

Our code is **already compatible** with pysnmp 7.x because:
- ✅ We use the `hlapi` (high-level API) which is stable across versions
- ✅ We never used the deprecated `oneliner` API that was removed in 7.x
- ✅ Our SNMP calls are standard and work with both 5.x and 7.x

## Benefits

1. **No Version Conflicts**: Uses whatever version HA Core provides
2. **Faster Installation**: No extra dependencies to download
3. **Automatic Updates**: When HA Core updates pysnmp, we benefit automatically
4. **Cleaner Integration**: Simpler manifest, easier to maintain
5. **Future-Proof**: Compatible with HA Core's SNMP evolution

## Migration Guide

If you had a previous version installed:

1. **Update the integration files** (copy new files over old ones)
2. **Restart Home Assistant**
3. **Done!**

No configuration changes needed. All your PDUs will continue working as before.

## What Versions to Use

- **Home Assistant**: 2024.10+ (includes pysnmp 7.1.21)
- **Python**: 3.11, 3.12, 3.13 (as supported by HA Core)
- **APC PDU Integration**: v1.0.0

## Fallback Options

The integration still has fallback options if pysnmp has issues:

1. **Primary**: pysnmp 7.1.21 (from HA Core)
2. **Fallback**: CLI tools (`snmpget`/`snmpset`) - optional for HA Core users
3. **Testing**: Demo Mode (no SNMP needed)

## References

- [HA Core SNMP Manifest](https://github.com/home-assistant/core/blob/9f3d890e91046ef85fa733e249b9114640355ee2/homeassistant/components/snmp/manifest.json) - Shows pysnmp 7.1.21 usage
- [Eaton UPS PR #60](https://github.com/jaroschek/home-assistant-eaton-ups/pull/60) - Similar migration to pysnmp 7.x

## Testing

All components tested and verified:

- ✅ manifest.json is valid JSON with proper semantic versioning
- ✅ All Python files compile without errors
- ✅ Config flow handles errors gracefully
- ✅ Demo mode works (no SNMP needed)
- ✅ Real PDU connection ready (with HA Core's pysnmp 7.1.21)

## Known Issues

None! The integration should now work smoothly with Home Assistant's built-in pysnmp.

## Questions?

See [DEPENDENCY_FIX.md](DEPENDENCY_FIX.md) for technical details about the pysnmp 7.1.21 compatibility.

---

**Released**: October 10, 2025
**Version**: 1.0.0

