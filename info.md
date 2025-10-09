# APC PDU Integration

Control your APC AP7920 and compatible PDUs directly from Home Assistant!

## Features

✅ **Easy UI Configuration** - No YAML editing required  
✅ **Individual Outlet Control** - Each outlet as a separate switch  
✅ **Master Switch** - Control all outlets at once  
✅ **Power Monitoring** - Real-time power consumption per outlet  
✅ **Device Grouping** - All entities grouped under one device  
✅ **Rich Attributes** - Outlet names, power usage, load state, and more  

## Quick Start

1. Install the integration via HACS
2. Restart Home Assistant
3. Go to Settings → Devices & Services
4. Click "Add Integration" and search for "APC PDU"
5. Enter your PDU IP address and SNMP community string
6. Done! All outlets will appear as switches

## Requirements

- APC PDU with SNMP enabled (AP7920, AP79xx series, etc.)
- SNMP community string with read-write access
- Network connectivity to the PDU

## Need Help?

See the full [README](https://github.com/vortitron/HAAPC) for detailed setup instructions, troubleshooting, and examples.

