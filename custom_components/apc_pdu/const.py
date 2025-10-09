"""Constants for the APC PDU integration."""

DOMAIN = "apc_pdu"

# Config entry keys
CONF_HOST = "host"
CONF_COMMUNITY = "community"
CONF_NAME = "name"
CONF_SNMP_VERSION = "snmp_version"

# Default values
DEFAULT_SNMP_VERSION = "1"
DEFAULT_SCAN_INTERVAL = 30

# SNMP OIDs - rPDU2 MIB (.1.3.6.1.4.1.318.1.1.12)
OID_BASE_RPDU2 = ".1.3.6.1.4.1.318.1.1.12"

# Device Identification
OID_PDU_NAME = f"{OID_BASE_RPDU2}.1.1.0"
OID_HARDWARE_REV = f"{OID_BASE_RPDU2}.1.2.0"
OID_FIRMWARE_REV = f"{OID_BASE_RPDU2}.1.3.0"
OID_MODEL = f"{OID_BASE_RPDU2}.1.5.0"
OID_SERIAL = f"{OID_BASE_RPDU2}.1.6.0"
OID_OUTLET_COUNT = f"{OID_BASE_RPDU2}.1.8.0"

# PDU Power Info
OID_RATED_VOLTAGE = f"{OID_BASE_RPDU2}.1.15.0"
OID_RATED_MAX_CURRENT = f"{OID_BASE_RPDU2}.1.17.0"
OID_PHASE_COUNT = f"{OID_BASE_RPDU2}.2.1.1.0"

# Bank Info
OID_BANK_LOAD_STATE = f"{OID_BASE_RPDU2}.2.3.1.1.3.1"

# Outlet Control (indexed by outlet number)
OID_OUTLET_CONTROL = f"{OID_BASE_RPDU2}.3.3.1.1.4"  # .X for outlet X

# Outlet Status (indexed by outlet number)
OID_OUTLET_NAME = f"{OID_BASE_RPDU2}.3.5.1.1.2"  # .X
OID_OUTLET_STATUS = f"{OID_BASE_RPDU2}.3.5.1.1.4"  # .X
OID_OUTLET_POWER = f"{OID_BASE_RPDU2}.3.5.1.1.7"  # .X (Watts)

# Fallback OIDs - MasterSwitch MIB (.1.3.6.1.4.1.318.1.1.4)
OID_BASE_MASTERSWITCH = ".1.3.6.1.4.1.318.1.1.4"
OID_MS_OUTLET_CONTROL = f"{OID_BASE_MASTERSWITCH}.4.2.1.3"  # .X
OID_MS_OUTLET_NAME = f"{OID_BASE_MASTERSWITCH}.4.2.1.4"  # .X
OID_MS_OUTLET_STATUS = f"{OID_BASE_MASTERSWITCH}.4.2.1.3"  # .X
OID_MS_OUTLET_COUNT = f"{OID_BASE_MASTERSWITCH}.4.1.0"

# SNMP Values
SNMP_OUTLET_ON = 1
SNMP_OUTLET_OFF = 2
SNMP_OUTLET_REBOOT = 3

# Status mapping
OUTLET_STATUS = {
    1: "On",
    2: "Off",
    3: "Rebooting",
}

BANK_LOAD_STATE = {
    1: "Low Load",
    2: "Normal",
    3: "Near Overload",
    4: "Overload",
}

