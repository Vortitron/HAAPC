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
