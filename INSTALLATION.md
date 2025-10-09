# Installation Guide

## Method 1: HACS (Recommended)

1. **Add Custom Repository**
   - Open HACS in Home Assistant
   - Click on "Integrations"
   - Click the three dots (⋮) in the top right corner
   - Select "Custom repositories"
   - Add repository URL: `https://github.com/vortitron/HAAPC`
   - Category: "Integration"
   - Click "Add"

2. **Install the Integration**
   - Find "APC PDU" in the HACS integration list
   - Click "Download"
   - Restart Home Assistant

3. **Configure**
   - Go to Settings → Devices & Services
   - Click "+ Add Integration"
   - Search for "APC PDU"
   - Follow the configuration steps

## Method 2: Manual Installation

1. **Download the Integration**
   ```bash
   cd /config
   git clone https://github.com/vortitron/HAAPC.git
   ```

2. **Copy to Custom Components**
   ```bash
   mkdir -p /config/custom_components
   cp -r /config/HAAPC/custom_components/apc_pdu /config/custom_components/
   ```

3. **Install Dependencies**
   Add to your `configuration.yaml` or let Home Assistant install automatically:
   ```bash
   pip install pysnmp==4.4.12
   ```

4. **Restart Home Assistant**

5. **Configure**
   - Go to Settings → Devices & Services
   - Click "+ Add Integration"
   - Search for "APC PDU"
   - Follow the configuration steps

## Configuration Details

When adding a PDU, you'll need:

| Field | Description | Example |
|-------|-------------|---------|
| **IP Address** | The IP address of your PDU | `192.168.1.28` |
| **SNMP Community** | SNMP community string (needs write access) | `private` or `5stream` |
| **Device Name** | Optional friendly name | `Server Room PDU` |
| **SNMP Version** | v1 or v2c | `1` (default) |

## Verifying SNMP Access

Before adding the integration, verify SNMP is working:

### Test SNMP Connection (Linux/Mac)
```bash
# Install snmp tools
sudo apt-get install snmp  # Ubuntu/Debian
brew install net-snmp      # macOS

# Test connection
snmpget -v1 -c YOUR_COMMUNITY YOUR_PDU_IP .1.3.6.1.4.1.318.1.1.12.1.5.0

# You should see the model number returned
```

### Test SNMP Connection (Windows)
Download and use [SnmpSoft Tools](http://www.snmpsoft.com/freetools/snmpget.html)

## Troubleshooting Installation

### Integration Not Showing Up
1. Ensure files are in `/config/custom_components/apc_pdu/`
2. Check Home Assistant logs for errors
3. Restart Home Assistant completely
4. Clear browser cache

### SNMP Connection Failed
1. Verify PDU IP address is correct and reachable
2. Check SNMP community string
3. Ensure SNMP is enabled on the PDU
4. Verify firewall allows UDP port 161
5. Try using SNMP v2c if v1 doesn't work

### Missing Power Data
- Some PDU models don't support per-outlet power monitoring
- Verify your PDU supports rPDU2 MIB
- Check outlets are under load

## Next Steps

After installation:
1. Check the Device page to see all entities
2. Add outlet switches to your dashboard
3. Set up automations
4. Monitor power consumption

For more help, see the [README](README.md) or [open an issue](https://github.com/vortitron/HAAPC/issues).

