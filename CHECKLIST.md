# Pre-Release Checklist

Use this checklist before publishing or testing the integration.

## ✅ File Structure

- [x] `custom_components/apc_pdu/__init__.py` - Main integration
- [x] `custom_components/apc_pdu/config_flow.py` - UI config
- [x] `custom_components/apc_pdu/const.py` - Constants
- [x] `custom_components/apc_pdu/coordinator.py` - Data coordinator
- [x] `custom_components/apc_pdu/manifest.json` - Metadata
- [x] `custom_components/apc_pdu/sensor.py` - Sensor platform
- [x] `custom_components/apc_pdu/snmp_client.py` - SNMP client
- [x] `custom_components/apc_pdu/strings.json` - UI strings
- [x] `custom_components/apc_pdu/switch.py` - Switch platform
- [x] `custom_components/apc_pdu/translations/en.json` - Translations

## ✅ HACS Files

- [x] `hacs.json` - HACS metadata
- [x] `info.md` - HACS store description
- [x] `README.md` - Main documentation
- [x] `LICENSE` - MIT License

## ✅ Documentation

- [x] `README.md` - Complete overview
- [x] `QUICKSTART.md` - 5-minute setup
- [x] `INSTALLATION.md` - Detailed install
- [x] `EXAMPLES.md` - Automation examples
- [x] `INTEGRATION_STRUCTURE.md` - Technical docs
- [x] `SUMMARY.md` - What was created
- [x] `CHECKLIST.md` - This file

## ✅ Code Quality

- [x] No linter errors
- [x] Valid JSON files (manifest, strings, hacs)
- [x] Python syntax valid
- [x] Proper imports
- [x] Type hints where appropriate
- [x] Error handling implemented

## ✅ Integration Features

### Configuration
- [x] UI-based config flow
- [x] SNMP connection validation
- [x] Unique ID from serial number
- [x] Error messages for common issues
- [x] Support for SNMP v1 and v2c

### Device
- [x] Device created with proper info
- [x] Manufacturer set (APC)
- [x] Model from SNMP
- [x] Serial number identifier
- [x] Firmware version
- [x] Hardware version

### Entities
- [x] Individual outlet switches (1-8)
- [x] Master switch (all outlets)
- [x] Power sensors per outlet
- [x] PDU status sensors
- [x] Device info sensors
- [x] Proper unique IDs
- [x] Entity naming with device name
- [x] Attributes populated

### Switch Entities
- [x] Turn on/off functionality
- [x] State tracking
- [x] Outlet number attribute
- [x] Outlet name attribute
- [x] Power attribute (if available)
- [x] Proper device association

### Master Switch
- [x] Controls all outlets
- [x] Total outlets attribute
- [x] Outlets on count
- [x] Total power attribute
- [x] Rated voltage attribute
- [x] Rated current attribute
- [x] Bank load state attribute

### Sensor Entities
- [x] Power sensors with device_class
- [x] State class for statistics
- [x] Proper units (W, V, A)
- [x] Device info sensors
- [x] Diagnostic entity category

### Data Updates
- [x] Coordinator pattern
- [x] 30-second polling
- [x] Error handling
- [x] Timeout handling
- [x] Retry logic

### SNMP
- [x] Get operations
- [x] Set operations
- [x] OID mapping
- [x] Value parsing
- [x] Error handling
- [x] Timeout configuration

## 🧪 Testing Checklist

### Installation Test
- [ ] Copy to Home Assistant custom_components
- [ ] Restart Home Assistant
- [ ] Check logs for errors
- [ ] Integration appears in UI

### Configuration Test
- [ ] Add integration via UI
- [ ] Enter valid IP and community
- [ ] Connection succeeds
- [ ] Device created
- [ ] Entities created

### Entity Test
- [ ] All outlet switches appear
- [ ] Master switch appears
- [ ] Power sensors appear
- [ ] Status sensors appear
- [ ] Device info sensors appear

### Control Test
- [ ] Outlet switch turns on
- [ ] Outlet switch turns off
- [ ] State reflects correctly
- [ ] PDU outlet actually changes
- [ ] Master switch controls all

### Data Test
- [ ] Power values update
- [ ] Outlet names correct
- [ ] Device info populated
- [ ] Attributes present
- [ ] Status updates every 30s

### Error Handling Test
- [ ] Invalid IP shows error
- [ ] Wrong community shows error
- [ ] Offline PDU handled gracefully
- [ ] SNMP timeout handled
- [ ] Invalid responses handled

### Multi-Device Test
- [ ] Can add second PDU
- [ ] Both PDUs work independently
- [ ] Unique IDs don't conflict
- [ ] Both appear as separate devices

### Reload Test
- [ ] Can reload integration
- [ ] Can unload integration
- [ ] Entities removed on unload
- [ ] Re-add works correctly

## 📝 Pre-Publish Checklist

### GitHub Repository
- [ ] Create GitHub repository
- [ ] Add all files
- [ ] Write good commit messages
- [ ] Create initial release (v1.0.0)
- [ ] Add topics/tags

### HACS Compatibility
- [ ] hacs.json present
- [ ] manifest.json valid
- [ ] README.md present
- [ ] Repository public
- [ ] Release created

### Documentation
- [ ] README complete
- [ ] Installation instructions clear
- [ ] Examples provided
- [ ] Troubleshooting section
- [ ] License file present

### Code Quality
- [ ] No hardcoded values
- [ ] Proper error messages
- [ ] Logging appropriate
- [ ] No security issues
- [ ] Dependencies listed

## 🚀 Publishing Steps

1. **Initialize Git**
   ```bash
   git init
   git add .
   git commit -m "Initial release - APC PDU HACS integration"
   ```

2. **Create GitHub Repo**
   - Go to GitHub
   - Create new repository "HAAPC"
   - Don't initialize with README (already exists)

3. **Push to GitHub**
   ```bash
   git remote add origin https://github.com/vortitron/HAAPC.git
   git branch -M main
   git push -u origin main
   ```

4. **Create Release**
   ```bash
   git tag -a v1.0.0 -m "Version 1.0.0 - Initial release"
   git push origin v1.0.0
   ```

5. **Test with HACS**
   - In Home Assistant, add custom repository
   - Install from HACS
   - Verify installation works
   - Test configuration

## 🎯 Version 1.0.0 Goals

### Must Have (All Complete ✅)
- [x] UI configuration
- [x] Device creation
- [x] Outlet switches
- [x] Power monitoring
- [x] Master switch
- [x] Proper device grouping
- [x] HACS compatible
- [x] Documentation

### Nice to Have (Future)
- [ ] SNMP v3 support
- [ ] Auto-discovery
- [ ] Configurable polling
- [ ] Reboot command
- [ ] Sequential power control
- [ ] Energy integration
- [ ] Parallel SNMP queries

## 📊 File Statistics

| Category | Files | Lines |
|----------|-------|-------|
| Python Code | 7 | ~1,000 |
| JSON Config | 4 | ~50 |
| Documentation | 7 | ~2,000 |
| **Total** | **18** | **~3,050** |

## ✅ Final Verification

Run these commands before publishing:

```bash
# Check Python syntax
python3 -m py_compile custom_components/apc_pdu/*.py

# Validate JSON
python3 -c "import json; json.load(open('custom_components/apc_pdu/manifest.json'))"
python3 -c "import json; json.load(open('custom_components/apc_pdu/strings.json'))"
python3 -c "import json; json.load(open('hacs.json'))"

# Check required files
ls custom_components/apc_pdu/__init__.py
ls custom_components/apc_pdu/manifest.json
ls README.md
ls LICENSE
ls hacs.json

# File count check (should be ~18)
find . -type f ! -path '*/\.*' ! -path '*/ap7920/*' ! -path '*/__pycache__/*' | wc -l
```

## 🎉 Ready to Publish?

If all items are checked:
1. ✅ All files present
2. ✅ Code quality verified
3. ✅ JSON files valid
4. ✅ Documentation complete
5. ✅ Testing done (or test plan ready)

**You're ready to publish! 🚀**

---

*Last Updated: 2025-10-09*

