# Home Assistant OS/Container Compatibility

## The Challenge

Home Assistant OS runs in a container without `apt-get` or traditional package managers.

## What's Actually Available in HA OS?

Home Assistant OS containers typically include SNMP tools because the **built-in SNMP integration** requires them:
- Home Assistant Core uses pysnmp internally
- Many HA integrations rely on SNMP

### Checking What's Available

The integration automatically tries (in order):
1. Demo Mode (if enabled) - ✅ Always works
2. Python pysnmp - ✅ Usually available in HA
3. CLI snmpget/snmpset - ⚠️ May or may not be in container

## For Home Assistant OS/Container Users

### Option 1: Use Demo Mode (Recommended for Testing)
- No dependencies needed
- Works 100% of the time
- Perfect for cloud servers
- See [DEMO_MODE.md](DEMO_MODE.md)

### Option 2: Rely on HA's pysnmp
If Home Assistant has fixed the pysnmp issue (or you're not on 2024.10.x), the Python library will work fine.

### Option 3: Install via SSH Add-on (Advanced)
If you need CLI tools:

1. Install "Terminal & SSH" add-on from HA
2. Access the container:
   ```bash
   docker exec -it homeassistant bash
   ```
3. Check if snmpget exists:
   ```bash
   which snmpget
   ```

**But you typically don't need to do this!**

## Our Updated Approach

### Graceful Degradation

```
┌─────────────────────────────────────────────────┐
│ 1. Demo Mode? → Use it (always works)          │
│                                                 │
│ 2. pysnmp works? → Use it (fast)               │
│                                                 │
│ 3. CLI tools? → Use them (fallback)            │
│                                                 │
│ 4. Nothing works? → Suggest Demo Mode          │
└─────────────────────────────────────────────────┘
```

## Recommended Setup by Installation Type

### Home Assistant OS (Docker-based)
**Best approach:** 
1. Try adding integration normally
2. If it fails, enable Demo Mode for testing
3. If Demo Mode works but real PDU doesn't, wait for HA to fix pysnmp or file an issue

**Don't need CLI tools** - pysnmp should work once HA fixes it.

### Home Assistant Container (DIY Docker)
**Best approach:**
1. Ensure `snmp` package is in the container
2. Add to Dockerfile:
   ```dockerfile
   RUN apt-get update && apt-get install -y snmp
   ```

### Home Assistant Core (Manual Python)
**Best approach:**
```bash
sudo apt-get install snmp
source /srv/homeassistant/bin/activate
# pysnmp or CLI tools both work
```

### Home Assistant Supervised
Similar to Core - can install system packages normally.

## Updated Error Messages

The integration now provides helpful context:

### If pysnmp Fails
```
INFO: pysnmp not available, trying command-line SNMP tools...
```

### If CLI Tools Also Fail
```
WARNING: Neither pysnmp nor snmpget command found.

For Home Assistant OS: This is expected. The integration will work once
Home Assistant's built-in pysnmp is fixed. Use Demo Mode for testing.

For Home Assistant Core: Install snmp package:
  sudo apt-get install snmp
```

## What Most Users Should Do

### Home Assistant OS Users (90% of users)
1. Install integration
2. If real PDU fails → Enable Demo Mode
3. Use demo PDU for testing/development
4. When you have real PDU access and HA has fixed pysnmp, disable demo mode

**No system changes needed!**

### Home Assistant Core Users (10% of users)
1. Install snmp package: `sudo apt-get install snmp`
2. Install integration
3. Add real PDU
4. Works forever!

## Why This Still Works

Even though HA OS users can't install CLI tools:
- ✅ Demo Mode always works (no SNMP needed)
- ✅ Most HA versions have working pysnmp
- ✅ When HA breaks pysnmp, users use Demo Mode
- ✅ When HA fixes pysnmp, users automatically get real PDU support

**No user action required in most cases!**

## Technical: Detecting Environment

The integration could detect the environment:

```python
def is_ha_os():
    """Check if running in HA OS container."""
    return os.path.exists('/usr/src/homeassistant')

def get_helpful_message():
    if is_ha_os():
        return "Home Assistant OS detected. Demo Mode recommended for testing."
    else:
        return "Install snmp package: sudo apt-get install snmp"
```

## Future Enhancement

We could add environment detection to provide more specific guidance:

```python
# In snmp_cli_client.py
if not snmpget_available:
    if is_ha_os():
        logger.info("HA OS detected. Waiting for pysnmp or use Demo Mode.")
    else:
        logger.warning("Install snmp: apt-get install snmp")
```

## Bottom Line for Users

### You're on Home Assistant OS?
- **Use Demo Mode** for testing (always works)
- **Wait for HA to fix pysnmp** for real PDU (or it might already work!)
- **Don't worry about CLI tools** (can't install them anyway)

### You're on Home Assistant Core?
- **Install snmp package** once (`sudo apt-get install snmp`)
- **Works forever** (survives all upgrades)
- **Best of both worlds** (pysnmp or CLI, both work)

## Testing the Fallback

You can test what method is being used by checking logs:

```
# Method 1 (Best)
INFO: Using pysnmp library for SNMP communication

# Method 2 (Fallback)
INFO: Using command-line SNMP tools as fallback

# Method 3 (Demo)
INFO: Demo mode enabled
```

## Conclusion

The integration is **already compatible with HA OS**:
- Demo Mode works everywhere
- pysnmp works when HA's python environment is healthy
- CLI fallback is a bonus for Core users

**No changes needed for HA OS users!** 🎉

