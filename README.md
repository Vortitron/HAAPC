# APC PDU Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)

A Home Assistant custom integration for controlling APC AP7920 and compatible PDUs (Power Distribution Units) via SNMP.

## Features

- **Easy Setup**: Add PDUs via the Home Assistant UI with just IP address and SNMP community string
- **Complete Device Integration**: All outlets grouped under a single device
- **Individual Outlet Control**: Each outlet appears as a switch entity
- **Master Switch**: Control all outlets at once
- **Power Monitoring**: Real-time power consumption per outlet (if supported by your PDU)
- **Device Information**: Model, serial number, firmware version, hardware version
- **PDU Status**: Rated voltage, max current, bank load state
- **Proper Device Grouping**: All entities properly grouped in Home Assistant's device view
- **Demo Mode**: Test the integration without physical hardware (perfect for cloud servers!)

## Supported Devices

- APC AP7920 (tested)
- APC AP79xx series with rPDU2 MIB support
- Other APC PDUs with SNMP support (may require minor adjustments)

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Click on "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add this repository URL: `https://github.com/vortitron/HAAPC`
6. Select category: "Integration"
7. Click "Add"
8. Find "APC PDU" in the integration list and install it
9. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/apc_pdu` directory to your Home Assistant's `custom_components` directory
2. Restart Home Assistant

## Configuration

1. Go to **Settings** → **Devices & Services**
2. Click **Add Integration**
3. Search for "APC PDU"
4. Enter your PDU details:
   - **IP Address**: The IP address of your PDU
   - **SNMP Community String**: Your SNMP community (default is usually "private" or "5stream")
   - **Device Name** (optional): A friendly name for your PDU
   - **SNMP Version**: Choose v1 or v2c (v1 is default)
   - **Demo Mode** (optional): Enable to test without real hardware (see [DEMO_MODE.md](DEMO_MODE.md))

## Entities Created

For each PDU, the integration creates:

### Switches
- **Outlet 1-8** (or however many outlets your PDU has): Individual outlet control
  - Attributes: `outlet_number`, `outlet_name`, `power_w` (if available)
- **Master Switch**: Control all outlets at once
  - Attributes: `total_outlets`, `outlets_on`, `total_power_w`, `rated_voltage`, `rated_max_current`, `bank_load_state`

### Sensors
- **Outlet X Power**: Power consumption for each outlet (Watts)
  - Attributes: `outlet_number`, `outlet_name`, `outlet_status`
- **Rated Voltage**: PDU rated voltage (V)
- **Rated Max Current**: PDU maximum current (A)
- **Bank Load State**: Current load state (Low Load, Normal, Near Overload, Overload)
- **Outlet Count**: Number of outlets
- **Hardware Version**: Device hardware revision
- **Firmware Version**: Device firmware version

## How It Works

This integration uses Home Assistant's SNMP infrastructure with a smart multi-tier approach:

1. **pysnmp.hlapi.v3arch.asyncio** (Primary): Uses HA's exact pysnmp import path
   - Async API wrapped with `asyncio.run()` for sync context
   - Factory pattern for proper async object creation
   - Matches HA's SNMP platform architecture

2. **Command-Line Tools** (Fallback): Uses system `snmpget`/`snmpset` if Python fails
   - For HA Core installations
   - Not available on HA OS/Container

3. **Demo Mode** (Testing): Simulates a PDU for testing
   - Tries real SNMP first (if available)
   - Falls back to simulation on timeout/failure
   - Perfect for development and testing

**Key insight**: We use the EXACT same pysnmp module path as Home Assistant's SNMP platform. If HA's SNMP integration works, ours will too!

The integration automatically selects the best available method, ensuring it works out-of-the-box on any Home Assistant installation.

## SNMP Configuration

Your PDU must have SNMP enabled. Typical SNMP settings:
- **Version**: SNMPv1 or SNMPv2c
- **Community String**: Usually "private" (read-write) or "public" (read-only - won't allow control)
- **Port**: 161 (default)

To configure SNMP on your APC PDU:
1. Access the PDU web interface or telnet/SSH
2. Navigate to Network → SNMP settings
3. Enable SNMP and set your community string
4. Ensure read-write access is granted

## Troubleshooting

### Connection Issues
- Verify the PDU IP address is correct and reachable
- Check that SNMP is enabled on the PDU
- Ensure the community string is correct
- Verify the SNMP version matches (v1 or v2c)
- Check firewall rules allow SNMP traffic (UDP port 161)

### No Power Readings
- Some PDU models don't support per-outlet power monitoring
- Verify your PDU model supports the rPDU2 MIB
- Check if outlets are actually drawing power
- Test with: `snmpwalk -v1 -c <community> <ip> .1.3.6.1.4.1.318.1.1.12.3.5.1.1.7`

### Outlets Not Controllable
- Ensure your SNMP community has write permissions
- Some PDUs require specific configuration to enable outlet control
- Check PDU settings for outlet control permissions

## Example Automations

### Turn on all outlets at sunrise
```yaml
automation:
  - alias: "PDU All On at Sunrise"
    trigger:
      - platform: sun
        event: sunrise
    action:
      - service: switch.turn_on
        target:
          entity_id: switch.apc_pdu_master_switch
```

### Alert on high power consumption
```yaml
automation:
  - alias: "PDU High Power Alert"
    trigger:
      - platform: numeric_state
        entity_id: switch.apc_pdu_master_switch
        attribute: total_power_w
        above: 1000
    action:
      - service: notify.notify
        data:
          message: "PDU power consumption is {{ state_attr('switch.apc_pdu_master_switch', 'total_power_w') }}W"
```

## Dependencies

This integration uses **pysnmp 7.1.21** provided by Home Assistant Core - no additional packages needed!

**How it works:**
1. **Demo Mode** - No SNMP needed (perfect for testing without hardware)
2. **Python pysnmp 7.1.21** - Home Assistant Core provides this automatically
3. **CLI fallback** - Uses system `snmpget`/`snmpset` if pysnmp has issues (optional)

**For most users**: Works out of the box! Home Assistant provides all required dependencies.

**For Home Assistant Core users** (optional): Install CLI tools for additional resilience:
```bash
sudo apt-get install snmp  # Debian/Ubuntu
sudo yum install net-snmp-utils  # RedHat/CentOS
```

**For Home Assistant OS/Container users**: No action needed! Everything works automatically with HA Core's built-in pysnmp 7.1.21.

See [DEPENDENCY_FIX.md](DEPENDENCY_FIX.md) for technical details about pysnmp 7.1.21 compatibility.

## Technical Details

### SNMP OIDs Used

The integration uses the APC rPDU2 MIB (`.1.3.6.1.4.1.318.1.1.12`):

- Device Info: `.1.1.0` - `.1.8.0`
- PDU Status: `.2.x.x.x`
- Outlet Control: `.3.3.1.1.4.X` (X = outlet number)
- Outlet Status: `.3.5.1.1.4.X`
- Outlet Power: `.3.5.1.1.7.X`

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Credits

Developed for use with APC AP7920 PDUs and Home Assistant.

## Support

For issues, questions, or suggestions, please [open an issue](https://github.com/vortitron/HAAPC/issues) on GitHub.
