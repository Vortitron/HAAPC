# Troubleshooting: "No module named 'pyasn1.compat.octets'"

## The Problem

Even after updating to `pysnmp-lextudio`, you're still seeing:
```
Error occurred loading flow for integration apc_pdu: No module named 'pyasn1.compat.octets'
```

## Why This Happens

Home Assistant may have:
1. Cached the old `pysnmp` dependency
2. Not fully removed the old integration files
3. Kept old `.pyc` files or `__pycache__` directories
4. Already installed the old dependency in its environment

## Solution: Clean Installation

### Step 1: Remove Old Integration Files

```bash
# On your Home Assistant machine
cd /config

# Remove the integration completely
rm -rf custom_components/apc_pdu

# Remove any cache files
find . -type d -name "__pycache__" -path "*/apc_pdu/*" -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -path "*/apc_pdu/*" -delete 2>/dev/null || true
```

### Step 2: Remove Old Dependency (if possible)

**For Home Assistant OS/Container** (most common):
```bash
# You typically can't/don't need to do this manually
# HA will handle it on restart
```

**For Home Assistant Core** (manual installation):
```bash
# Activate your HA virtual environment first
source /srv/homeassistant/bin/activate

# Remove old pysnmp
pip3 uninstall -y pysnmp pyasn1-modules pyasn1

# Install the new one
pip3 install pysnmp-lextudio==5.0.34
```

### Step 3: Copy Updated Integration

```bash
# Copy the updated integration with the new manifest.json
cd /home/vortitron/HAAPC
sudo cp -r custom_components/apc_pdu /config/custom_components/

# Verify manifest.json has correct dependency
grep -A1 requirements /config/custom_components/apc_pdu/manifest.json
# Should show: "requirements": ["pysnmp-lextudio==5.0.34"]
```

### Step 4: Full Restart

**Important**: Do a FULL restart, not just a configuration reload!

```bash
# Via Home Assistant UI:
# Settings → System → Restart (wait for full reboot)

# OR via CLI:
ha core restart

# OR via Docker:
docker restart homeassistant
```

### Step 5: Clear Browser Cache

Sometimes the integration config flow is cached in your browser:

```
1. Open Home Assistant
2. Press Ctrl+Shift+R (or Cmd+Shift+R on Mac)
3. Or clear browser cache completely
```

### Step 6: Add Integration

Now try adding the integration:
1. Settings → Devices & Services
2. Add Integration → "APC PDU"
3. Enable **Demo Mode** for testing
4. Fill in dummy values and submit

## Alternative: Use Demo Mode Only (Bypasses SNMP)

If you just want to test on your cloud server, you can temporarily modify the code to skip SNMP import for demo mode:

### Quick Fix for Demo Mode Testing

Edit `/config/custom_components/apc_pdu/snmp_client.py`:

Add this at the top after the imports:
```python
# Add this right after the existing imports, around line 17
try:
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
except ImportError:
    # SNMP not available - only demo mode will work
    pass
```

This way demo mode will work even if SNMP dependencies fail, but you won't be able to use real PDUs.

## Verification Steps

After restart, check these:

### 1. Check Logs
```bash
# Look for successful setup
tail -f /config/home-assistant.log | grep apc_pdu
```

You should see:
```
✅ "Setting up apc_pdu component"
```

NOT:
```
❌ "No module named 'pyasn1.compat.octets'"
```

### 2. Verify Dependency Installed

**Home Assistant OS/Container**:
Check in the logs after restart - HA will log dependency installation

**Home Assistant Core**:
```bash
source /srv/homeassistant/bin/activate
pip3 list | grep pysnmp
# Should show: pysnmp-lextudio    5.0.34
```

### 3. Check manifest.json

```bash
cat /config/custom_components/apc_pdu/manifest.json | grep -A1 requirements
```

Should output:
```json
"requirements": ["pysnmp-lextudio==5.0.34"],
```

## Complete Clean Installation Script

Here's a complete script to do everything:

```bash
#!/bin/bash
# Run this on your Home Assistant machine

echo "=== Cleaning old installation ==="
cd /config
rm -rf custom_components/apc_pdu
find . -type d -name "__pycache__" -path "*/apc_pdu/*" -exec rm -rf {} + 2>/dev/null || true

echo "=== Copying updated integration ==="
# Adjust this path to where you have the files
cp -r /home/vortitron/HAAPC/custom_components/apc_pdu custom_components/

echo "=== Verifying manifest ==="
grep requirements custom_components/apc_pdu/manifest.json

echo "=== Done! Now restart Home Assistant ==="
echo "After restart, add the integration with Demo Mode enabled"
```

## Still Not Working?

### Option 1: Manual Dependency Installation

Before restarting HA, manually install the dependency:

**Find your HA Python path:**
```bash
which python3
# or
ps aux | grep "home-assistant"
```

**Install dependency:**
```bash
/usr/local/bin/python3 -m pip install pysnmp-lextudio==5.0.34
# Adjust path based on your installation
```

### Option 2: Use Demo Mode Only

If you're on a cloud server and only need demo mode:

1. Test with demo mode first (doesn't need SNMP)
2. Deal with real PDU dependencies later
3. Demo mode is perfect for testing automations anyway

### Option 3: Check Home Assistant Version

```bash
ha core info
```

Make sure you're on Home Assistant 2024.1.0 or newer. Older versions might have dependency issues.

## Common Mistakes

❌ **Only reloading integrations** - Not enough, need full restart
❌ **Not removing old files** - Cache persists
❌ **Wrong manifest.json** - Still has old pysnmp
❌ **Not waiting for full reboot** - HA needs to fully restart
❌ **Browser cache** - Clear it!

## Success Checklist

Before trying to add the integration:

- [ ] Old integration files removed
- [ ] New integration files copied
- [ ] manifest.json shows `pysnmp-lextudio==5.0.34`
- [ ] Home Assistant fully restarted (not just reloaded)
- [ ] Browser cache cleared
- [ ] Logs show no import errors
- [ ] Ready to add integration!

## Questions?

**Q: Can I just use demo mode?**
A: Yes! Demo mode doesn't use SNMP at all, so it works even if dependencies fail.

**Q: Do I need pysnmp for demo mode?**
A: Technically no, but HA tries to import it anyway. Use the import try/except fix above.

**Q: Can I use the old pysnmp?**
A: No, it's broken with Python 3.11+. You need pysnmp-lextudio.

**Q: What if I can't remove the old dependency?**
A: Try the demo-mode-only approach with the try/except import.

---

**Most Common Solution**: Remove integration files, restart HA fully, copy new files, restart again, then add integration with demo mode.

