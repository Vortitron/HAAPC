# Testing SNMP Connection to Your PDU

## Step 1: Verify Network Connectivity

From your Home Assistant server:

```bash
# Test if PDU is reachable
ping -c 4 192.168.1.28

# Test if SNMP port is open
nc -zv 192.168.1.28 161

# OR
nmap -p 161 192.168.1.28
```

## Step 2: Test SNMP with Command Line Tools

Install SNMP tools if not already installed:

```bash
# Ubuntu/Debian
sudo apt-get install snmp snmp-mibs-downloader

# Then test
snmpget -v1 -c 5stream 192.168.1.28 .1.3.6.1.4.1.318.1.1.12.1.5.0
```

**Expected output**: Should return the model number like "AP7920"

If this fails, the issue is SNMP configuration, not our integration.

## Step 3: Fix HA 2024.10.x pysnmp Bug

Since demo mode works but real PDU doesn't, the pysnmp libraries are partially working but failing during execution. You need to fix the system pysnmp:

### For Home Assistant Core:

```bash
# Activate HA virtual environment
source /srv/homeassistant/bin/activate

# Check current pysnmp version
pip3 list | grep -E "pysnmp|pyasn1"

# Clean install (this fixes the HA 2024.10.x bug)
pip3 uninstall -y pysnmp pyasn1 pysmi pysnmpcrypto pysnmp-lextudio pysmi-lextudio

pip3 install pysnmp==6.2.6
pip3 install pyasn1==0.6.0

# Restart Home Assistant
systemctl restart home-assistant@homeassistant

# OR
ha core restart
```

### For Home Assistant OS/Container:

This is trickier since you can't easily access the Python environment. Try:

```bash
# Access the container/OS
# (method varies by installation)

# Then run similar commands
pip3 uninstall -y pysnmp pyasn1 pysmi pysnmpcrypto
pip3 install pysnmp==6.2.6 pyasn1==0.6.0
```

## Step 4: Check Home Assistant Logs

After applying the fix and restarting:

```bash
# Watch logs
tail -f /config/home-assistant.log | grep -i snmp

# Or check in UI:
# Settings → System → Logs
# Filter for "snmp" or "apc_pdu"
```

## Step 5: Try Adding PDU Again

After fixing pysnmp:

1. Settings → Devices & Services
2. Add Integration → "APC PDU"
3. Fill in:
   - IP: `192.168.1.28`
   - Community: `5stream`
   - Name: `cAPC3`
   - Demo Mode: ❌ **UNCHECK**
4. Submit

## Common Issues & Solutions

### Issue: "Failed to connect" but network is fine

**Cause**: HA 2024.10.x pysnmp bug - imports work but execution fails

**Solution**: Apply the pysnmp fix (Step 3)

### Issue: SNMP tools work, but integration doesn't

**Cause**: Virtual environment has different pysnmp version

**Solution**: Make sure you're fixing pysnmp in the correct virtual environment where HA runs

### Issue: "Permission denied" on SNMP

**Cause**: SNMP community has read-only permissions

**Solution**: Set PDU SNMP community to "Read-Write"

### Issue: Connection times out

**Cause**: Firewall blocking UDP 161

**Solution**: 
```bash
sudo ufw allow 161/udp
# OR check iptables
```

## Quick Diagnostic Script

Save this as `test_snmp.py` and run in your HA environment:

```python
#!/usr/bin/env python3
import sys

print("Testing pysnmp installation...")

try:
    from pysnmp.hlapi import (
        CommunityData,
        ContextData,
        ObjectIdentity,
        ObjectType,
        SnmpEngine,
        UdpTransportTarget,
        getCmd,
    )
    print("✅ pysnmp imports successful")
except ImportError as e:
    print(f"❌ pysnmp import failed: {e}")
    sys.exit(1)

print("\nTesting SNMP connection to PDU...")

# Test connection
try:
    iterator = getCmd(
        SnmpEngine(),
        CommunityData('5stream', mpModel=0),
        UdpTransportTarget(('192.168.1.28', 161), timeout=5, retries=2),
        ContextData(),
        ObjectType(ObjectIdentity('.1.3.6.1.4.1.318.1.1.12.1.5.0'))
    )
    
    error_indication, error_status, error_index, var_binds = next(iterator)
    
    if error_indication:
        print(f"❌ SNMP Error: {error_indication}")
    elif error_status:
        print(f"❌ SNMP Status Error: {error_status}")
    else:
        for var_bind in var_binds:
            print(f"✅ SNMP working! Model: {var_bind[1]}")
            
except Exception as e:
    print(f"❌ Connection failed: {e}")
    import traceback
    traceback.print_exc()
```

Run it:
```bash
source /srv/homeassistant/bin/activate
python3 test_snmp.py
```

## Expected Results

**If pysnmp is broken:**
```
✅ pysnmp imports successful
❌ Connection failed: No module named 'pyasn1.compat.octets'
```

**If pysnmp is fixed but SNMP config wrong:**
```
✅ pysnmp imports successful
❌ SNMP Error: timeout
```

**If everything works:**
```
✅ pysnmp imports successful
✅ SNMP working! Model: AP7920
```

## The Most Likely Issue

Based on your symptoms (demo works, real PDU fails with "Failed to connect"):

**The HA 2024.10.x pysnmp bug is still active**

Even though imports work (so demo loads), the actual SNMP calls fail when executed.

**Solution**: Apply Step 3 (fix system pysnmp) then retry.

## Alternative: Temporary pysnmp Fix in Integration

If you can't fix the system pysnmp, I can modify the integration to use an alternative SNMP method, but it's better to fix the system issue since it affects all SNMP integrations.

## After Fixing

Once pysnmp is fixed:
1. All SNMP integrations (Brother, built-in SNMP, etc.) will work again
2. You can add real PDUs without Demo Mode
3. You can mix real and demo PDUs in same HA instance

## Need More Help?

Share the output of:
```bash
# From HA environment
pip3 list | grep -E "pysnmp|pyasn1"
python3 test_snmp.py
tail -n 50 /config/home-assistant.log | grep -i "apc_pdu\|snmp"
```

