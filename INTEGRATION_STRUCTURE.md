# APC PDU Integration Structure

This document outlines the complete structure of the APC PDU HACS integration.

## Directory Structure

```
HAAPC/
├── custom_components/
│   └── apc_pdu/
│       ├── __init__.py              # Main integration setup
│       ├── config_flow.py           # UI configuration flow
│       ├── const.py                 # Constants and OIDs
│       ├── coordinator.py           # Data update coordinator
│       ├── manifest.json            # Integration metadata
│       ├── sensor.py                # Sensor entities
│       ├── snmp_client.py           # SNMP communication
│       ├── strings.json             # UI strings
│       ├── switch.py                # Switch entities
│       └── translations/
│           └── en.json              # English translations
├── ap7920/                          # Original YAML configs (reference)
├── EXAMPLES.md                      # Usage examples and automations
├── hacs.json                        # HACS metadata
├── info.md                          # HACS info page
├── INSTALLATION.md                  # Installation instructions
├── INTEGRATION_STRUCTURE.md         # This file
├── LICENSE                          # MIT License
├── QUICKSTART.md                    # Quick start guide
└── README.md                        # Main documentation
```

## Core Components

### 1. `__init__.py` - Integration Setup
- Handles integration lifecycle (setup, unload, reload)
- Registers platforms (switch, sensor)
- Creates coordinator instance

### 2. `config_flow.py` - Configuration Flow
- UI-based configuration
- SNMP connection validation
- Unique ID management (serial number)
- Error handling

### 3. `const.py` - Constants
- SNMP OIDs for rPDU2 MIB
- Default values
- Status mappings
- Configuration keys

### 4. `coordinator.py` - Data Coordinator
- Periodic SNMP polling (30 second default)
- Data aggregation
- Error handling and retry logic

### 5. `snmp_client.py` - SNMP Client
- SNMP get/set operations
- Device info retrieval
- Outlet control
- Status queries
- Power monitoring

### 6. `switch.py` - Switch Entities
- Individual outlet switches (1-8)
- Master switch (all outlets)
- State tracking
- Attributes (power, name, etc.)

### 7. `sensor.py` - Sensor Entities
- Per-outlet power sensors
- Device info sensors
- PDU status sensors (voltage, current, load state)

### 8. `manifest.json` - Metadata
- Integration domain
- Dependencies (pysnmp)
- Version
- Documentation links

## Entities Created

### Switches (9 total for 8-outlet PDU)
| Entity ID | Description | Attributes |
|-----------|-------------|------------|
| `switch.apc_pdu_outlet_1` | Outlet 1 control | outlet_number, outlet_name, power_w |
| `switch.apc_pdu_outlet_2` | Outlet 2 control | outlet_number, outlet_name, power_w |
| ... | ... | ... |
| `switch.apc_pdu_outlet_8` | Outlet 8 control | outlet_number, outlet_name, power_w |
| `switch.apc_pdu_master_switch` | All outlets control | total_outlets, outlets_on, total_power_w, rated_voltage, rated_max_current, bank_load_state |

### Sensors (12+ total)
| Entity ID | Description | Unit | Device Class |
|-----------|-------------|------|--------------|
| `sensor.apc_pdu_outlet_1_power` | Outlet 1 power | W | power |
| `sensor.apc_pdu_outlet_2_power` | Outlet 2 power | W | power |
| ... | ... | ... | ... |
| `sensor.apc_pdu_outlet_8_power` | Outlet 8 power | W | power |
| `sensor.apc_pdu_rated_voltage` | PDU rated voltage | V | voltage |
| `sensor.apc_pdu_rated_max_current` | PDU max current | A | current |
| `sensor.apc_pdu_bank_load_state` | Load state | - | - |
| `sensor.apc_pdu_outlet_count` | Number of outlets | - | - |
| `sensor.apc_pdu_hardware_version` | Hardware version | - | diagnostic |
| `sensor.apc_pdu_firmware_version` | Firmware version | - | diagnostic |

## Device Information

Each PDU appears as a single device with:
- **Identifiers**: Serial number
- **Manufacturer**: APC
- **Model**: From SNMP (e.g., "AP7920")
- **SW Version**: Firmware version
- **HW Version**: Hardware version

## SNMP OIDs Used

### Device Identification
- Name: `.1.3.6.1.4.1.318.1.1.12.1.1.0`
- Hardware: `.1.3.6.1.4.1.318.1.1.12.1.2.0`
- Firmware: `.1.3.6.1.4.1.318.1.1.12.1.3.0`
- Model: `.1.3.6.1.4.1.318.1.1.12.1.5.0`
- Serial: `.1.3.6.1.4.1.318.1.1.12.1.6.0`
- Outlet Count: `.1.3.6.1.4.1.318.1.1.12.1.8.0`

### Outlet Control (per outlet X)
- Control: `.1.3.6.1.4.1.318.1.1.12.3.3.1.1.4.X`
- Name: `.1.3.6.1.4.1.318.1.1.12.3.5.1.1.2.X`
- Status: `.1.3.6.1.4.1.318.1.1.12.3.5.1.1.4.X`
- Power: `.1.3.6.1.4.1.318.1.1.12.3.5.1.1.7.X`

### PDU Status
- Rated Voltage: `.1.3.6.1.4.1.318.1.1.12.1.15.0`
- Rated Max Current: `.1.3.6.1.4.1.318.1.1.12.1.17.0`
- Bank Load State: `.1.3.6.1.4.1.318.1.1.12.2.3.1.1.3.1`

## Configuration Options

| Option | Type | Required | Default | Description |
|--------|------|----------|---------|-------------|
| host | string | Yes | - | PDU IP address |
| community | string | Yes | "private" | SNMP community string |
| name | string | No | Model name | Friendly device name |
| snmp_version | string | No | "1" | SNMP version (1 or 2c) |

## Data Flow

```
┌─────────────────┐
│  Home Assistant │
└────────┬────────┘
         │
         │ Config Entry
         ▼
┌─────────────────┐
│   Coordinator   │◄──── Updates every 30s
└────────┬────────┘
         │
         │ Uses
         ▼
┌─────────────────┐
│   SNMP Client   │
└────────┬────────┘
         │
         │ SNMP v1/v2c
         │ UDP Port 161
         ▼
┌─────────────────┐
│    APC PDU      │
└─────────────────┘
```

## Update Cycle

1. Coordinator polls every 30 seconds
2. SNMP Client queries:
   - Device info (once, cached)
   - PDU status (voltage, current, load state)
   - All outlet statuses (name, state, power)
3. Data aggregated into coordinator data
4. Entities update from coordinator data
5. State changes trigger HA updates

## Control Flow (Switch Operation)

```
User toggles switch
    ↓
Switch entity async_turn_on/off
    ↓
SNMP Client set_outlet()
    ↓
SNMP SET command to PDU
    ↓
Wait for completion
    ↓
Request coordinator refresh
    ↓
New state appears in UI
```

## Error Handling

- **Connection Errors**: Logged, coordinator marks update failed
- **SNMP Timeouts**: 5 second timeout, 2 retries
- **Invalid Responses**: Gracefully handled, null values returned
- **Config Flow Errors**: User-friendly error messages

## Performance Considerations

- **Polling Interval**: 30 seconds (configurable via const.py)
- **SNMP Timeout**: 5 seconds per request
- **Concurrent Requests**: All outlets queried in sequence (could be parallelized)
- **Data Caching**: Device info cached in coordinator

## Dependencies

- **pysnmp**: 4.4.12 (SNMP protocol implementation)
- **Home Assistant**: 2024.1.0+ (uses modern config flow, coordinator patterns)

## Upgrade Path from YAML

To migrate from YAML configuration:

1. Install the integration
2. Add PDU via UI
3. Verify entities work
4. Remove YAML configuration
5. Restart Home Assistant
6. Update automation entity IDs if needed

Old YAML entities like `sensor.capc3_outlet_1_name` become:
- `switch.apc_pdu_outlet_1` (switch)
- `sensor.apc_pdu_outlet_1_power` (power sensor)

## Testing Checklist

- [ ] Connection validation works
- [ ] Device info retrieved correctly
- [ ] All outlets discovered
- [ ] Switches control outlets
- [ ] Power values update
- [ ] Master switch controls all outlets
- [ ] Attributes populated correctly
- [ ] Error handling works
- [ ] Reload/unload works
- [ ] Multiple PDUs can be added

## Future Enhancements

Potential improvements:
- [ ] Support for MasterSwitch MIB fallback
- [ ] Configurable polling interval
- [ ] Outlet grouping/templates
- [ ] Reboot command support
- [ ] Sequential power on/off scripts
- [ ] Energy monitoring integration
- [ ] SNMP v3 support
- [ ] Parallel SNMP queries
- [ ] Auto-discovery via mDNS/SSDP

## Documentation Files

- **README.md**: Main documentation, features, overview
- **QUICKSTART.md**: 5-minute setup guide
- **INSTALLATION.md**: Detailed installation steps
- **EXAMPLES.md**: Automation examples, dashboard cards
- **INTEGRATION_STRUCTURE.md**: This file - technical details

## Support

- GitHub: https://github.com/vortitron/HAAPC
- Issues: https://github.com/vortitron/HAAPC/issues
- HACS: Available as custom repository

## Version History

- **1.0.0**: Initial release
  - UI configuration
  - Switch entities for outlets
  - Sensor entities for power monitoring
  - Master switch
  - Device grouping
  - Full SNMP support

