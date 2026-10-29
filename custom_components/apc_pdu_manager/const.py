"""Constants for the APC PDU integration."""

from __future__ import annotations

from typing import Final

DOMAIN: Final = "apc_pdu_manager"
MANUFACTURER: Final = "APC"

# Config entry data keys (host and port use the homeassistant.const names)
CONF_COMMUNITY: Final = "community"
CONF_SNMP_VERSION: Final = "snmp_version"
CONF_AUTH_PROTOCOL: Final = "auth_protocol"
CONF_AUTH_KEY: Final = "auth_key"
CONF_PRIV_PROTOCOL: Final = "priv_protocol"
CONF_PRIV_KEY: Final = "priv_key"

SNMP_VERSION_1: Final = "1"
SNMP_VERSION_2C: Final = "2c"
SNMP_VERSION_3: Final = "3"
SNMP_VERSIONS: Final = [SNMP_VERSION_1, SNMP_VERSION_2C, SNMP_VERSION_3]

AUTH_NONE: Final = "none"
AUTH_PROTOCOLS: Final = [AUTH_NONE, "md5", "sha", "sha224", "sha256", "sha384", "sha512"]
PRIV_NONE: Final = "none"
PRIV_PROTOCOLS: Final = [PRIV_NONE, "des", "3des", "aes", "aes192", "aes256"]

DEFAULT_PORT: Final = 161
DEFAULT_COMMUNITY: Final = "private"
DEFAULT_SNMP_VERSION: Final = SNMP_VERSION_1
DEFAULT_SCAN_INTERVAL: Final = 30
MIN_SCAN_INTERVAL: Final = 10
MAX_SCAN_INTERVAL: Final = 3600

# Which PowerNet-MIB branch a PDU is driven through
MIB_RPDU: Final = "rpdu"
MIB_RPDU2: Final = "rpdu2"
MIB_SPDU: Final = "spdu"

# --- APC PowerNet-MIB, rPDU branch (.1.3.6.1.4.1.318.1.1.12) ---
# Used by Switched Rack PDUs such as the AP79xx series.
_RPDU: Final = "1.3.6.1.4.1.318.1.1.12"

# rPDUIdent
OID_PDU_NAME: Final = f"{_RPDU}.1.1.0"
OID_HARDWARE_REV: Final = f"{_RPDU}.1.2.0"
OID_FIRMWARE_REV: Final = f"{_RPDU}.1.3.0"
OID_MODEL: Final = f"{_RPDU}.1.5.0"
OID_SERIAL: Final = f"{_RPDU}.1.6.0"
OID_DEVICE_RATING: Final = f"{_RPDU}.1.7.0"  # amps
OID_OUTLET_COUNT: Final = f"{_RPDU}.1.8.0"
OID_LINE_VOLTAGE: Final = f"{_RPDU}.1.15.0"  # configured nominal volts
OID_POWER_WATTS: Final = f"{_RPDU}.1.16.0"  # not on every model / firmware

# rPDULoadDevice
OID_NUM_PHASES: Final = f"{_RPDU}.2.1.2.0"
OID_NUM_BANKS: Final = f"{_RPDU}.2.1.4.0"

# rPDULoadStatusTable, indexed by phase/bank entry (phases first, then banks)
OID_LOAD_CURRENT: Final = f"{_RPDU}.2.3.1.1.2"  # tenths of amps
OID_LOAD_STATE: Final = f"{_RPDU}.2.3.1.1.3"
OID_LOAD_PHASE: Final = f"{_RPDU}.2.3.1.1.4"
OID_LOAD_BANK: Final = f"{_RPDU}.2.3.1.1.5"

# rPDUOutletDevice
OID_MONITORED_OUTLETS: Final = f"{_RPDU}.3.1.5.0"

# rPDUOutletControlTable / rPDUOutletStatusTable, indexed by outlet number
OID_OUTLET_COMMAND: Final = f"{_RPDU}.3.3.1.1.4"
OID_OUTLET_NAME: Final = f"{_RPDU}.3.5.1.1.2"
OID_OUTLET_STATE: Final = f"{_RPDU}.3.5.1.1.4"
OID_OUTLET_CURRENT: Final = f"{_RPDU}.3.5.1.1.7"  # tenths of amps, metered models

OUTLET_STATE_ON: Final = 1
OUTLET_STATE_OFF: Final = 2
OUTLET_COMMAND_ON: Final = 1  # immediateOn
OUTLET_COMMAND_OFF: Final = 2  # immediateOff

# rPDULoadStatusLoadState
LOAD_STATES: Final = {
    1: "normal",
    2: "low",
    3: "near_overload",
    4: "overload",
}

# --- rPDU2 branch (.1.3.6.1.4.1.318.1.1.26) ---
# Switched Rack PDUs from the AP84xx, AP86xx, AP88xx and AP89xx ranges. Every
# table is indexed by row; daisy-chained PDUs share the tables, and the module
# column says which PDU a row belongs to.
_RPDU2: Final = "1.3.6.1.4.1.318.1.1.26"

# rPDU2IdentTable
OID2_IDENT_MODULE: Final = f"{_RPDU2}.2.1.2"
OID2_IDENT_NAME: Final = f"{_RPDU2}.2.1.3"
OID2_IDENT_HARDWARE_REV: Final = f"{_RPDU2}.2.1.5"
OID2_IDENT_FIRMWARE_REV: Final = f"{_RPDU2}.2.1.6"
OID2_IDENT_MODEL: Final = f"{_RPDU2}.2.1.8"
OID2_IDENT_SERIAL: Final = f"{_RPDU2}.2.1.9"

# rPDU2DevicePropertiesTable / rPDU2DeviceStatusTable
OID2_DEVICE_SWITCHED_OUTLETS: Final = f"{_RPDU2}.4.2.1.5"
OID2_DEVICE_METERED_OUTLETS: Final = f"{_RPDU2}.4.2.1.6"
OID2_DEVICE_MAX_CURRENT: Final = f"{_RPDU2}.4.2.1.9"  # amps
OID2_DEVICE_POWER: Final = f"{_RPDU2}.4.3.1.5"  # hundredths of kW, -1 unsupported
OID2_DEVICE_ENERGY: Final = f"{_RPDU2}.4.3.1.9"  # tenths of kWh, -1 unsupported

# Table sizes, across every PDU in a chain
OID2_PHASE_TABLE_SIZE: Final = f"{_RPDU2}.5.0"
OID2_BANK_TABLE_SIZE: Final = f"{_RPDU2}.7.0"
OID2_SWITCHED_TABLE_SIZE: Final = f"{_RPDU2}.9.1.0"
OID2_METERED_TABLE_SIZE: Final = f"{_RPDU2}.9.3.0"

# rPDU2PhaseStatusTable
OID2_PHASE_MODULE: Final = f"{_RPDU2}.6.3.1.2"
OID2_PHASE_NUMBER: Final = f"{_RPDU2}.6.3.1.3"
OID2_PHASE_LOAD_STATE: Final = f"{_RPDU2}.6.3.1.4"
OID2_PHASE_CURRENT: Final = f"{_RPDU2}.6.3.1.5"  # tenths of amps
OID2_PHASE_VOLTAGE: Final = f"{_RPDU2}.6.3.1.6"  # volts, -1 unsupported

# rPDU2BankStatusTable
OID2_BANK_MODULE: Final = f"{_RPDU2}.8.3.1.2"
OID2_BANK_NUMBER: Final = f"{_RPDU2}.8.3.1.3"
OID2_BANK_LOAD_STATE: Final = f"{_RPDU2}.8.3.1.4"
OID2_BANK_CURRENT: Final = f"{_RPDU2}.8.3.1.5"  # tenths of amps

# rPDU2OutletSwitchedStatusTable / rPDU2OutletSwitchedControlTable
OID2_OUTLET_MODULE: Final = f"{_RPDU2}.9.2.3.1.2"
OID2_OUTLET_NAME: Final = f"{_RPDU2}.9.2.3.1.3"
OID2_OUTLET_NUMBER: Final = f"{_RPDU2}.9.2.3.1.4"
OID2_OUTLET_STATE: Final = f"{_RPDU2}.9.2.3.1.5"
OID2_OUTLET_COMMAND: Final = f"{_RPDU2}.9.2.4.1.5"

# rPDU2OutletMeteredStatusTable
OID2_METERED_MODULE: Final = f"{_RPDU2}.9.4.3.1.2"
OID2_METERED_NUMBER: Final = f"{_RPDU2}.9.4.3.1.4"
OID2_METERED_CURRENT: Final = f"{_RPDU2}.9.4.3.1.6"  # tenths of amps

# rPDU2OutletSwitchedStatusState is off (1) / on (2), the reverse of rPDU
OUTLET2_STATE_OFF: Final = 1
OUTLET2_STATE_ON: Final = 2

# rPDU2PhaseStatusLoadState / rPDU2BankStatusLoadState: low and normal are
# numbered the other way round from rPDU
LOAD_STATES2: Final = {
    1: "low",
    2: "normal",
    3: "near_overload",
    4: "overload",
}

# --- sPDU branch (.1.3.6.1.4.1.318.1.1.4) ---
# MasterSwitch units that predate rPDU. They switch outlets but report no load.
_SPDU: Final = "1.3.6.1.4.1.318.1.1.4"

OIDS_HARDWARE_REV: Final = f"{_SPDU}.1.1.0"
OIDS_FIRMWARE_REV: Final = f"{_SPDU}.1.2.0"
OIDS_MODEL: Final = f"{_SPDU}.1.4.0"
OIDS_SERIAL: Final = f"{_SPDU}.1.5.0"
OIDS_OUTLET_COUNT: Final = f"{_SPDU}.4.1.0"
# sPDUOutletCtl: reads the state (1 on, 2 off), writes the command (1 on, 2 off)
OIDS_OUTLET_CTL: Final = f"{_SPDU}.4.2.1.3"
OIDS_OUTLET_NAME: Final = f"{_SPDU}.4.2.1.4"
