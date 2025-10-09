# Quick Start Guide

Get your APC PDU integrated with Home Assistant in 5 minutes!

## Prerequisites

✓ APC AP7920 or compatible PDU  
✓ PDU connected to your network  
✓ SNMP enabled on the PDU  
✓ SNMP community string (usually "private" or check your PDU settings)  

## Step 1: Enable SNMP on Your PDU

If not already enabled:

1. Access your PDU's web interface (e.g., http://192.168.1.28)
2. Login with your credentials
3. Go to **Configuration** → **Network** → **SNMP**
4. Enable SNMP v1 or v2c
5. Set or note your community string (default often "private")
6. Ensure **Access Type** is set to **Read-Write**
7. Click **Apply**

## Step 2: Install the Integration

### Option A: Via HACS (Easiest)

1. Open **HACS** in Home Assistant
2. Go to **Integrations**
3. Click the **⋮** menu → **Custom repositories**
4. Add repository: `https://github.com/vortitron/HAAPC`
5. Category: **Integration**
6. Click **Add**
7. Find **APC PDU** in the list
8. Click **Download**
9. **Restart Home Assistant**

### Option B: Manual

1. Copy `custom_components/apc_pdu/` to your HA config directory
2. Restart Home Assistant

## Step 3: Add Your PDU

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for **APC PDU**
4. Enter your information:
   - **IP Address**: `192.168.1.28` (your PDU's IP)
   - **SNMP Community**: `private` (or your community string)
   - **Device Name**: `Server Room PDU` (optional, friendly name)
   - **SNMP Version**: `1` (or `2c` if that's what you use)
5. Click **Submit**

## Step 4: Verify It Works

1. Go to **Settings** → **Devices & Services** → **Devices**
2. Find your PDU device
3. You should see:
   - 8 outlet switches (Outlet 1-8)
   - 1 master switch
   - Multiple sensors (power, voltage, etc.)

## Step 5: Add to Dashboard

### Quick Method
1. Go to your dashboard
2. Click **Edit Dashboard**
3. Click **+ Add Card**
4. Choose **Entities**
5. Search for your PDU outlets
6. Select the ones you want
7. Click **Add**

### Example Card
```yaml
type: entities
title: PDU Control
entities:
  - entity: switch.apc_pdu_outlet_1
  - entity: switch.apc_pdu_outlet_2
  - entity: switch.apc_pdu_outlet_3
  - entity: switch.apc_pdu_master_switch
```

## Test It!

1. Click an outlet switch to turn it on/off
2. Watch the outlet status change on your PDU
3. Check the power sensor for consumption data

## What's Next?

- **View Power Usage**: Check the power sensors for each outlet
- **Create Automations**: Set schedules, alerts, etc.
- **Explore Examples**: See [EXAMPLES.md](EXAMPLES.md) for automation ideas

## Troubleshooting

### Can't Find the Integration?
- Make sure you restarted Home Assistant after installation
- Check `custom_components/apc_pdu/` exists
- Look in HA logs for errors

### "Cannot Connect" Error?
- Verify PDU IP address: `ping 192.168.1.28`
- Check SNMP is enabled on PDU
- Verify community string is correct
- Test SNMP: `snmpget -v1 -c private 192.168.1.28 .1.3.6.1.4.1.318.1.1.12.1.5.0`

### Outlets Don't Control?
- Community string needs **Read-Write** access
- Check PDU settings for outlet control permissions
- Some PDUs require outlet control to be explicitly enabled

### No Power Data?
- Not all PDU models support per-outlet power monitoring
- Verify your PDU model (AP7920 should support it with rPDU2 MIB)
- Ensure outlets are actually drawing power

## Getting Help

- **Documentation**: [README.md](README.md)
- **Examples**: [EXAMPLES.md](EXAMPLES.md)
- **Installation**: [INSTALLATION.md](INSTALLATION.md)
- **Issues**: [GitHub Issues](https://github.com/vortitron/HAAPC/issues)

## Common First Automations

### Turn All Off at Night
```yaml
automation:
  - alias: "PDU Off at Midnight"
    trigger:
      platform: time
        at: "00:00:00"
    action:
      service: switch.turn_off
        target:
          entity_id: switch.apc_pdu_master_switch
```

### Power Usage Alert
```yaml
automation:
  - alias: "High Power Alert"
    trigger:
      platform: numeric_state
        entity_id: switch.apc_pdu_master_switch
        attribute: total_power_w
        above: 1000
    action:
      service: notify.notify
        data:
          message: "PDU power usage is high: {{ state_attr('switch.apc_pdu_master_switch', 'total_power_w') }}W"
```

---

**You're all set! Enjoy controlling your PDU from Home Assistant! 🎉**

