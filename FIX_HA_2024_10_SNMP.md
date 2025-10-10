# Fix for Home Assistant 2024.10.x SNMP Issue

## The Problem

If you're getting this error:
```
No module named 'pyasn1.compat.octets'
```

This is a **known bug in Home Assistant 2024.10.x** that affects ALL SNMP-based integrations, not just ours.

**References:**
- [Home Assistant Community Discussion](https://community.home-assistant.io/t/the-snmp-integration-does-not-work-after-upgrade-to-2024-10-x/781434)
- [GitHub Issue](https://github.com/jaroschek/home-assistant-eaton-epdu/issues/22)
- [Stack Overflow](https://stackoverflow.com/questions/16303512/pysnmp-importerror-no-module-named-pyasn1-compat-octets)

## Root Cause

Home Assistant 2024.10.x includes `pysnmp==6.2.6` for its built-in SNMP integration, which has broken `pyasn1` dependencies. This affects:
- Built-in SNMP integration
- Brother Printer integration
- Any custom integration using SNMP (including ours)

## Solutions

### Solution 1: Use Demo Mode (Recommended for Cloud Servers)

**Demo mode doesn't use SNMP at all**, so it works perfectly regardless of this bug:

1. Install the integration
2. When adding device, **check "Demo Mode"**
3. Fill in any values (they won't be used)
4. Enjoy a fully working PDU simulation!

See [DEMO_MODE.md](DEMO_MODE.md) for details.

### Solution 2: Fix System pysnmp (For Real PDU Usage)

This fixes the system-wide issue so all SNMP integrations work:

#### For Home Assistant OS/Container

```bash
# Access the container/system
# (method depends on your installation)

# Fix the dependencies
pip3 uninstall -y pysnmp pyasn1 pysmi pysnmpcrypto
pip3 install --upgrade pysnmp==6.2.6
pip3 install --upgrade pyasn1==0.6.0

# Restart Home Assistant
```

#### For Home Assistant Core

```bash
# Activate your HA virtual environment
source /srv/homeassistant/bin/activate

# Uninstall all pysnmp-related packages
pip3 uninstall -y pysnmp pyasn1 pysmi pysnmpcrypto pysnmp-lextudio pysmi-lextudio

# Reinstall with correct versions
pip3 install --upgrade pysnmp==6.2.6

# Restart Home Assistant
systemctl restart home-assistant@homeassistant
```

#### One-Line Fix (Core Installation)

From the [community solution](https://community.home-assistant.io/t/the-snmp-integration-does-not-work-after-upgrade-to-2024-10-x/781434):

```bash
pip3 uninstall -y pysnmp pyasn1 pysmi pysnmpcrypto pysnmp-lextudio pysmi-lextudio && pip3 install --upgrade pysnmp==6.2.6
```

### Solution 3: Downgrade Home Assistant (Temporary)

If you can't fix pysnmp and need real PDU access:

```bash
# Downgrade to 2024.9.3 (last working version)
# This is temporary until HA fixes the issue
```

### Solution 4: Wait for Home Assistant Fix

The Home Assistant team is aware of this issue. A fix should come in a future release (2024.10.2+).

## Which Solution Should I Use?

| Situation | Recommended Solution |
|-----------|---------------------|
| **Testing on cloud server** | Solution 1: Demo Mode ✅ |
| **Need real PDU now** | Solution 2: Fix pysnmp |
| **Multiple SNMP integrations broken** | Solution 2: Fix pysnmp |
| **Don't want to mess with dependencies** | Solution 1: Demo Mode or Solution 3: Downgrade |
| **Can wait** | Solution 4: Wait for HA update |

## Verification

After applying Solution 2, verify it worked:

```bash
# Check installed versions
pip3 list | grep -E "pysnmp|pyasn1"

# Should show:
# pysnmp        6.2.6
# pyasn1        (latest or 0.6.0)

# Try adding integration - should work now
```

## Our Integration's Improvements

We've made our integration more resilient:

1. **Lazy SNMP import** - Only loads pysnmp when actually needed
2. **Better error messages** - Tells you exactly what's wrong
3. **Demo mode fallback** - Works without any SNMP dependencies
4. **Clear instructions** - This document!

## Why This Affects Our Integration

Even though we use `pysnmp-lextudio` in our `manifest.json`, Home Assistant's dependency resolver finds the system-wide `pysnmp==6.2.6` first (installed by HA's built-in SNMP integration), which has the broken dependencies.

## Timeline

- **HA 2024.9.3** - Last working version ✅
- **HA 2024.10.0** - Bug introduced ❌
- **HA 2024.10.1** - Bug still present ❌
- **HA 2024.10.2+** - Fix expected 🤞

## Community Workarounds

From the Home Assistant community, these worked for others:

### Workaround A (koala's solution)
```bash
pip3 uninstall pysnmp pyasn1 pysmi pysnmpcrypto pysnmp-lextudio pysmi-lextudio
pip3 install --upgrade pysnmp==6.2.6
```

### Workaround B (PrairieSnpr's solution)
```bash
pip3 install pyasn1==0.6.0
```

### Workaround C (parautenbach's solution)
```bash
pip3 install --upgrade pyasn1
```

## For Home Assistant Core Users

If you're maintaining your own Core installation, you're responsible for dependencies. The fix is:

```bash
# In your HA virtual environment
source /srv/homeassistant/bin/activate

# Clean install
pip3 uninstall -y pysnmp pyasn1 pysmi pysnmpcrypto pysnmp-lextudio pysmi-lextudio
pip3 install pysnmp==6.2.6

# Restart HA
systemctl restart home-assistant@homeassistant
```

## Quick Test with Demo Mode

Want to test if the integration works without fixing pysnmp?

1. Add integration
2. **Enable Demo Mode** ✅
3. Use any IP/community (won't be used)
4. Integration loads successfully
5. Get fully working PDU with 8 outlets

## Additional Resources

- **Our Integration Docs**: [README.md](README.md)
- **Demo Mode Guide**: [DEMO_MODE.md](DEMO_MODE.md)
- **General Troubleshooting**: [INSTALL_TROUBLESHOOTING.md](INSTALL_TROUBLESHOOTING.md)
- **HA Community Discussion**: https://community.home-assistant.io/t/781434
- **GitHub Issue**: https://github.com/jaroschek/home-assistant-eaton-epdu/issues/22

## TL;DR

**Quick Fix for Cloud Servers**: Use Demo Mode - it bypasses SNMP entirely!

**Quick Fix for Real PDU**: 
```bash
pip3 uninstall -y pysnmp pyasn1 pysmi pysnmpcrypto pysnmp-lextudio pysmi-lextudio
pip3 install --upgrade pysnmp==6.2.6
systemctl restart home-assistant@homeassistant
```

This is a Home Assistant bug, not an issue with our integration. We've made our integration work around it with Demo Mode! 🎉

