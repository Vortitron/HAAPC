"""Async SNMP client for APC Switched Rack PDUs (PowerNet-MIB rPDU, rPDU2 and sPDU)."""

from __future__ import annotations

import asyncio
import ipaddress
import logging
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from functools import partial
from typing import Any

from pyasn1.type import univ
from pysnmp.error import PySnmpError
from pysnmp.proto import errind
from pysnmp.proto.rfc1902 import Integer

try:  # pysnmp 7.x (Home Assistant 2025.8 and later)
    from pysnmp.hlapi.v3arch.asyncio import (
        CommunityData,
        ContextData,
        ObjectIdentity,
        ObjectType,
        SnmpEngine,
        Udp6TransportTarget,
        UdpTransportTarget,
        UsmUserData,
        get_cmd,
        set_cmd,
        usm3DESEDEPrivProtocol,
        usmAesCfb128Protocol,
        usmAesCfb192Protocol,
        usmAesCfb256Protocol,
        usmDESPrivProtocol,
        usmHMAC128SHA224AuthProtocol,
        usmHMAC192SHA256AuthProtocol,
        usmHMAC256SHA384AuthProtocol,
        usmHMAC384SHA512AuthProtocol,
        usmHMACMD5AuthProtocol,
        usmHMACSHAAuthProtocol,
        usmNoAuthProtocol,
        usmNoPrivProtocol,
    )

    PYSNMP_7 = True
except ImportError:  # pysnmp 6.x (Home Assistant up to 2025.7)
    from pysnmp.hlapi.asyncio import (  # type: ignore[no-redef]
        CommunityData,
        ContextData,
        ObjectIdentity,
        ObjectType,
        SnmpEngine,
        Udp6TransportTarget,
        UdpTransportTarget,
        UsmUserData,
        usm3DESEDEPrivProtocol,
        usmAesCfb128Protocol,
        usmAesCfb192Protocol,
        usmAesCfb256Protocol,
        usmDESPrivProtocol,
        usmHMAC128SHA224AuthProtocol,
        usmHMAC192SHA256AuthProtocol,
        usmHMAC256SHA384AuthProtocol,
        usmHMAC384SHA512AuthProtocol,
        usmHMACMD5AuthProtocol,
        usmHMACSHAAuthProtocol,
        usmNoAuthProtocol,
        usmNoPrivProtocol,
    )
    from pysnmp.hlapi.asyncio import (
        getCmd as get_cmd,
    )
    from pysnmp.hlapi.asyncio import (
        setCmd as set_cmd,
    )

    PYSNMP_7 = False

from .const import (
    AUTH_NONE,
    DEFAULT_PORT,
    LOAD_STATES,
    LOAD_STATES2,
    MIB_RPDU,
    MIB_RPDU2,
    MIB_SPDU,
    OID2_BANK_CURRENT,
    OID2_BANK_LOAD_STATE,
    OID2_BANK_MODULE,
    OID2_BANK_NUMBER,
    OID2_BANK_TABLE_SIZE,
    OID2_DEVICE_ENERGY,
    OID2_DEVICE_MAX_CURRENT,
    OID2_DEVICE_METERED_OUTLETS,
    OID2_DEVICE_POWER,
    OID2_DEVICE_SWITCHED_OUTLETS,
    OID2_IDENT_FIRMWARE_REV,
    OID2_IDENT_HARDWARE_REV,
    OID2_IDENT_MODEL,
    OID2_IDENT_MODULE,
    OID2_IDENT_NAME,
    OID2_IDENT_SERIAL,
    OID2_METERED_CURRENT,
    OID2_METERED_MODULE,
    OID2_METERED_NUMBER,
    OID2_METERED_TABLE_SIZE,
    OID2_OUTLET_COMMAND,
    OID2_OUTLET_MODULE,
    OID2_OUTLET_NAME,
    OID2_OUTLET_NUMBER,
    OID2_OUTLET_STATE,
    OID2_PHASE_CURRENT,
    OID2_PHASE_LOAD_STATE,
    OID2_PHASE_MODULE,
    OID2_PHASE_NUMBER,
    OID2_PHASE_TABLE_SIZE,
    OID2_PHASE_VOLTAGE,
    OID2_SWITCHED_TABLE_SIZE,
    OIDS_FIRMWARE_REV,
    OIDS_HARDWARE_REV,
    OIDS_MODEL,
    OIDS_OUTLET_COUNT,
    OIDS_OUTLET_CTL,
    OIDS_OUTLET_NAME,
    OIDS_SERIAL,
    OID_DEVICE_RATING,
    OID_FIRMWARE_REV,
    OID_HARDWARE_REV,
    OID_LINE_VOLTAGE,
    OID_LOAD_BANK,
    OID_LOAD_CURRENT,
    OID_LOAD_PHASE,
    OID_LOAD_STATE,
    OID_MODEL,
    OID_MONITORED_OUTLETS,
    OID_NUM_BANKS,
    OID_NUM_PHASES,
    OID_OUTLET_COMMAND,
    OID_OUTLET_COUNT,
    OID_OUTLET_CURRENT,
    OID_OUTLET_NAME,
    OID_OUTLET_STATE,
    OID_PDU_NAME,
    OID_POWER_WATTS,
    OID_SERIAL,
    OUTLET2_STATE_OFF,
    OUTLET2_STATE_ON,
    OUTLET_COMMAND_OFF,
    OUTLET_COMMAND_ON,
    OUTLET_STATE_OFF,
    OUTLET_STATE_ON,
    PRIV_NONE,
    SNMP_VERSION_1,
    SNMP_VERSION_2C,
    SNMP_VERSION_3,
)

_LOGGER = logging.getLogger(__name__)

# Keep requests small: old network management cards answer slowly and
# SNMPv1 responses are limited in size.
MAX_VARBINDS_PER_REQUEST = 10

_AUTH_PROTOCOLS = {
    AUTH_NONE: usmNoAuthProtocol,
    "md5": usmHMACMD5AuthProtocol,
    "sha": usmHMACSHAAuthProtocol,
    "sha224": usmHMAC128SHA224AuthProtocol,
    "sha256": usmHMAC192SHA256AuthProtocol,
    "sha384": usmHMAC256SHA384AuthProtocol,
    "sha512": usmHMAC384SHA512AuthProtocol,
}
_PRIV_PROTOCOLS = {
    PRIV_NONE: usmNoPrivProtocol,
    "des": usmDESPrivProtocol,
    "3des": usm3DESEDEPrivProtocol,
    "aes": usmAesCfb128Protocol,
    "aes192": usmAesCfb192Protocol,
    "aes256": usmAesCfb256Protocol,
}

# SNMP error-status values (RFC 1157 / RFC 3416)
_ERROR_STATUS = {
    1: "tooBig",
    2: "noSuchName",
    3: "badValue",
    4: "readOnly",
    5: "genErr",
    6: "noAccess",
    7: "wrongType",
    8: "wrongLength",
    9: "wrongEncoding",
    10: "wrongValue",
    11: "noCreation",
    12: "inconsistentValue",
    13: "resourceUnavailable",
    14: "commitFailed",
    15: "undoFailed",
    16: "authorizationError",
    17: "notWritable",
    18: "inconsistentName",
}
_TOO_BIG = 1
_NO_SUCH_NAME = 2

# Error indications that mean the SNMPv3 credentials were rejected
_AUTH_ERRORS: tuple[type, ...] = tuple(
    cls
    for name in (
        "UnknownUserName",
        "WrongDigest",
        "DecryptionError",
        "UnknownSecurityName",
        "UnsupportedSecLevel",
        "UnsupportedSecurityLevel",
        "AuthenticationError",
        "AuthenticationFailure",
    )
    if isinstance(cls := getattr(errind, name, None), type)
)


class APCPDUError(Exception):
    """Base error for the PDU client."""


class CannotConnect(APCPDUError):
    """The PDU did not answer (wrong host, port, community or network)."""


class InvalidAuth(APCPDUError):
    """The PDU rejected the SNMPv3 credentials."""


class NotSupported(APCPDUError):
    """The device answered but does not look like an APC switched PDU."""


class CommandFailed(APCPDUError):
    """The PDU rejected a SET request."""


@dataclass(frozen=True)
class SNMPAuth:
    """Credentials for one PDU."""

    version: str = SNMP_VERSION_1
    community: str | None = None
    username: str | None = None
    auth_protocol: str = AUTH_NONE
    auth_key: str | None = None
    priv_protocol: str = PRIV_NONE
    priv_key: str | None = None


@dataclass(frozen=True)
class LoadEntry:
    """One row of rPDULoadStatusTable (a phase or a bank)."""

    index: int
    phase: int | None = None
    bank: int | None = None
    # Row in the rPDU2 phase or bank table
    row: int | None = None


@dataclass
class PDUInfo:
    """Static information read once when the PDU is set up."""

    model: str | None
    serial: str | None
    name: str | None
    firmware: str | None
    hardware: str | None
    outlet_count: int
    rated_current: int | None = None
    nominal_voltage: int | None = None
    has_power: bool = False
    has_outlet_current: bool = False
    has_voltage: bool = False
    has_energy: bool = False
    loads: list[LoadEntry] = field(default_factory=list)
    mib: str = MIB_RPDU
    # rPDU2 only: outlet number -> row in the switched / metered outlet tables
    outlet_rows: dict[int, int] = field(default_factory=dict)
    metered_rows: dict[int, int] = field(default_factory=dict)

    @property
    def outlet_numbers(self) -> list[int]:
        """Numbers of the switched outlets."""
        if self.outlet_rows:
            return sorted(self.outlet_rows)
        return list(range(1, self.outlet_count + 1))

    @property
    def metered_outlets(self) -> list[int]:
        """Numbers of the outlets that report their own current."""
        if self.mib == MIB_RPDU2:
            return sorted(n for n in self.metered_rows if n in self.outlet_rows)
        return self.outlet_numbers if self.has_outlet_current else []


@dataclass
class OutletStatus:
    """State of one outlet."""

    name: str | None
    is_on: bool | None
    current: float | None = None


@dataclass
class PDUStatus:
    """Values that change and are polled."""

    outlets: dict[int, OutletStatus]
    load_current: dict[int, float | None] = field(default_factory=dict)
    load_state: dict[int, str | None] = field(default_factory=dict)
    voltage: dict[int, int | None] = field(default_factory=dict)
    power: int | None = None
    energy: float | None = None  # kWh, rPDU2 only


def _convert(value: Any) -> Any:
    """Convert a pysnmp value to a plain Python value, None when absent."""
    if value is None or isinstance(value, univ.Null):
        # Null also covers noSuchObject / noSuchInstance / endOfMibView
        return None
    if isinstance(value, univ.Integer):
        return int(value)
    if isinstance(value, univ.OctetString):
        return value.asOctets().decode("utf-8", "replace").strip("\x00").strip()
    return value.prettyPrint()


def _as_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _non_negative(value: Any) -> int | None:
    """rPDU2 reports -1 for a value the model does not measure."""
    number = _as_int(value)
    return number if number is not None and number >= 0 else None


def _switch_state(value: Any, on: int, off: int) -> bool | None:
    state = _as_int(value)
    if state == on:
        return True
    if state == off:
        return False
    return None


def _tenths(value: Any) -> float | None:
    if (number := _as_int(value)) is None:
        return None
    return round(number / 10, 1)


def _is_ipv6(host: str) -> bool:
    try:
        return ipaddress.ip_address(host.strip("[]")).version == 6
    except ValueError:
        return False


def _create_engine() -> SnmpEngine:
    """Create an SNMP engine and load its MIBs (blocking, run in an executor)."""
    engine = SnmpEngine()
    try:
        if PYSNMP_7:
            from pysnmp.smi import view  # noqa: PLC0415

            controller = view.MibViewController(
                engine.message_dispatcher.mib_instrum_controller.get_mib_builder()
            )
            engine.cache["mibViewController"] = controller
            controller.mibBuilder.load_modules()
        else:
            from pysnmp.hlapi.asyncio.cmdgen import vbProcessor  # noqa: PLC0415

            builder = vbProcessor.getMibViewController(engine).mibBuilder
            if "PYSNMP-MIB" not in builder.mibSymbols:
                builder.loadModules()
    except Exception:  # noqa: BLE001 - preloading is an optimisation only
        _LOGGER.debug("Could not preload pysnmp MIB modules", exc_info=True)
    return engine


class APCPDUClient:
    """Talks to one PDU. All methods are coroutines and never block the loop."""

    def __init__(
        self,
        host: str,
        auth: SNMPAuth,
        port: int = DEFAULT_PORT,
        timeout: float = 3,
        retries: int = 1,
    ) -> None:
        """Initialise the client; no network traffic happens here."""
        self.host = host
        self.port = port
        self._auth = auth
        self._timeout = timeout
        self._retries = retries
        self._engine: SnmpEngine | None = None
        self._target: Any = None
        self._auth_data: Any = None
        self._lock = asyncio.Lock()
        self._info: PDUInfo | None = None

    def _build_auth_data(self) -> Any:
        auth = self._auth
        if auth.version == SNMP_VERSION_3:
            auth_protocol = auth.auth_protocol or AUTH_NONE
            priv_protocol = auth.priv_protocol or PRIV_NONE
            if auth_protocol == AUTH_NONE:
                priv_protocol = PRIV_NONE  # privacy requires authentication
            return UsmUserData(
                auth.username or "",
                authKey=auth.auth_key if auth_protocol != AUTH_NONE else None,
                privKey=auth.priv_key if priv_protocol != PRIV_NONE else None,
                authProtocol=_AUTH_PROTOCOLS[auth_protocol],
                privProtocol=_PRIV_PROTOCOLS[priv_protocol],
            )
        mp_model = 0 if auth.version == SNMP_VERSION_1 else 1
        if auth.version not in (SNMP_VERSION_1, SNMP_VERSION_2C):
            raise ValueError(f"Unsupported SNMP version {auth.version}")
        return CommunityData(auth.community or "", mpModel=mp_model)

    async def _async_ensure_ready(self) -> None:
        if self._target is not None:
            return
        loop = asyncio.get_running_loop()
        try:
            self._auth_data = self._build_auth_data()
        except PySnmpError as err:  # e.g. key shorter than 8 characters
            raise InvalidAuth(str(err)) from err
        if self._engine is None:
            self._engine = await loop.run_in_executor(None, _create_engine)
        target_cls = Udp6TransportTarget if _is_ipv6(self.host) else UdpTransportTarget
        address = (self.host.strip("[]"), self.port)
        try:
            if PYSNMP_7:
                self._target = await target_cls.create(
                    address, timeout=self._timeout, retries=self._retries
                )
            else:
                # pysnmp 6 resolves the host name synchronously
                self._target = await loop.run_in_executor(
                    None,
                    partial(
                        target_cls,
                        address,
                        timeout=self._timeout,
                        retries=self._retries,
                    ),
                )
        except PySnmpError as err:
            raise CannotConnect(f"Cannot resolve {self.host}: {err}") from err

    async def _async_request(
        self, command: Callable[..., Any], *var_binds: Any
    ) -> tuple[int, Sequence[Any]]:
        """Send one request and return (error status, var binds)."""
        async with self._lock:
            await self._async_ensure_ready()
            try:
                error_indication, error_status, _, result = await command(
                    self._engine, self._auth_data, self._target, ContextData(), *var_binds
                )
            except PySnmpError as err:
                raise CannotConnect(str(err)) from err
        if error_indication:
            if isinstance(error_indication, _AUTH_ERRORS):
                raise InvalidAuth(str(error_indication))
            if isinstance(error_indication, errind.RequestTimedOut):
                raise CannotConnect(f"No SNMP response from {self.host}:{self.port}")
            raise CannotConnect(str(error_indication))
        return int(error_status or 0), result

    async def async_get(self, oids: Sequence[str]) -> dict[str, Any]:
        """Read OIDs; OIDs the PDU does not implement map to None."""
        values: dict[str, Any] = {}
        for start in range(0, len(oids), MAX_VARBINDS_PER_REQUEST):
            values.update(
                await self._async_get_chunk(oids[start : start + MAX_VARBINDS_PER_REQUEST])
            )
        return values

    async def _async_get_chunk(self, oids: Sequence[str]) -> dict[str, Any]:
        status, var_binds = await self._async_request(
            get_cmd, *(ObjectType(ObjectIdentity(oid)) for oid in oids)
        )
        if not status:
            return {
                oid: _convert(var_bind[1]) for oid, var_bind in zip(oids, var_binds, strict=False)
            }
        if len(oids) > 1 and status in (_NO_SUCH_NAME, _TOO_BIG):
            # SNMPv1 fails the whole request when one OID is missing
            values: dict[str, Any] = {}
            for oid in oids:
                values.update(await self._async_get_chunk([oid]))
            return values
        if status == _NO_SUCH_NAME:
            return {oids[0]: None}
        raise APCPDUError(f"PDU returned SNMP error {_ERROR_STATUS.get(status, status)}")

    async def async_set_int(self, oid: str, value: int) -> None:
        """Write an integer OID."""
        status, _ = await self._async_request(
            set_cmd, ObjectType(ObjectIdentity(oid), Integer(value))
        )
        if status:
            raise CommandFailed(_ERROR_STATUS.get(status, str(status)))

    async def async_get_info(self) -> PDUInfo:
        """Identify the PDU and work out which optional values it provides.

        rPDU is tried first, so PDUs that also answer the older sPDU tables
        (most AP79xx) keep the readings rPDU adds.
        """
        info = (
            await self._async_get_rpdu_info()
            or await self._async_get_rpdu2_info()
            or await self._async_get_spdu_info()
        )
        if info is None:
            raise NotSupported(
                f"{self.host} answered but does not expose the APC rPDU, rPDU2 or sPDU MIB"
            )
        self._info = info
        return info

    async def _async_get_rpdu_info(self) -> PDUInfo | None:
        ident = await self.async_get(
            [
                OID_MODEL,
                OID_SERIAL,
                OID_OUTLET_COUNT,
                OID_PDU_NAME,
                OID_FIRMWARE_REV,
                OID_HARDWARE_REV,
            ]
        )
        outlet_count = _as_int(ident[OID_OUTLET_COUNT])
        if not ident[OID_MODEL] or not outlet_count or outlet_count < 1:
            _LOGGER.debug(
                "%s has no rPDU MIB (model=%r, outlets=%r)",
                self.host,
                ident[OID_MODEL],
                ident[OID_OUTLET_COUNT],
            )
            return None
        extra = await self.async_get(
            [
                OID_DEVICE_RATING,
                OID_LINE_VOLTAGE,
                OID_POWER_WATTS,
                OID_NUM_PHASES,
                OID_NUM_BANKS,
                OID_MONITORED_OUTLETS,
            ]
        )
        entries = (_as_int(extra[OID_NUM_PHASES]) or 0) + (_as_int(extra[OID_NUM_BANKS]) or 0)
        indexes = list(range(1, entries + 1)) or [1]
        load_values = await self.async_get(
            [
                f"{oid}.{index}"
                for index in indexes
                for oid in (OID_LOAD_CURRENT, OID_LOAD_PHASE, OID_LOAD_BANK)
            ]
        )
        loads = [
            LoadEntry(
                index=index,
                phase=_as_int(load_values[f"{OID_LOAD_PHASE}.{index}"]),
                bank=_as_int(load_values[f"{OID_LOAD_BANK}.{index}"]),
            )
            for index in indexes
            if load_values[f"{OID_LOAD_CURRENT}.{index}"] is not None
        ]
        return PDUInfo(
            model=ident[OID_MODEL],
            serial=ident[OID_SERIAL] or None,
            name=ident[OID_PDU_NAME] or None,
            firmware=ident[OID_FIRMWARE_REV] or None,
            hardware=ident[OID_HARDWARE_REV] or None,
            outlet_count=outlet_count,
            rated_current=_as_int(extra[OID_DEVICE_RATING]),
            nominal_voltage=_as_int(extra[OID_LINE_VOLTAGE]),
            has_power=extra[OID_POWER_WATTS] is not None,
            has_outlet_current=(_as_int(extra[OID_MONITORED_OUTLETS]) or 0) > 0,
            loads=loads,
        )

    async def _async_get_rpdu2_info(self) -> PDUInfo | None:
        # Row 1 of the ident and device tables is the PDU at this address;
        # PDUs daisy-chained behind it are left out.
        ident = await self.async_get(
            [
                f"{oid}.1"
                for oid in (
                    OID2_IDENT_MODEL,
                    OID2_IDENT_SERIAL,
                    OID2_IDENT_NAME,
                    OID2_IDENT_FIRMWARE_REV,
                    OID2_IDENT_HARDWARE_REV,
                    OID2_IDENT_MODULE,
                )
            ]
        )
        if not (model := ident[f"{OID2_IDENT_MODEL}.1"]):
            _LOGGER.debug("%s has no rPDU2 MIB", self.host)
            return None
        module = _as_int(ident[f"{OID2_IDENT_MODULE}.1"])
        extra = await self.async_get(
            [
                f"{OID2_DEVICE_SWITCHED_OUTLETS}.1",
                f"{OID2_DEVICE_METERED_OUTLETS}.1",
                f"{OID2_DEVICE_MAX_CURRENT}.1",
                f"{OID2_DEVICE_POWER}.1",
                f"{OID2_DEVICE_ENERGY}.1",
                OID2_PHASE_TABLE_SIZE,
                OID2_BANK_TABLE_SIZE,
                OID2_SWITCHED_TABLE_SIZE,
                OID2_METERED_TABLE_SIZE,
            ]
        )
        switched = _as_int(extra[f"{OID2_DEVICE_SWITCHED_OUTLETS}.1"]) or 0
        metered = _as_int(extra[f"{OID2_DEVICE_METERED_OUTLETS}.1"]) or 0
        outlet_rows = await self._async_rows(
            _as_int(extra[OID2_SWITCHED_TABLE_SIZE]) or switched,
            OID2_OUTLET_MODULE,
            OID2_OUTLET_NUMBER,
            module,
        )
        if not outlet_rows:
            _LOGGER.debug("%s (%s) has no switched outlets", self.host, model)
            return None
        metered_rows = (
            await self._async_rows(
                _as_int(extra[OID2_METERED_TABLE_SIZE]) or metered,
                OID2_METERED_MODULE,
                OID2_METERED_NUMBER,
                module,
            )
            if metered
            else {}
        )
        phase_rows = await self._async_rows(
            _as_int(extra[OID2_PHASE_TABLE_SIZE]) or 1,
            OID2_PHASE_MODULE,
            OID2_PHASE_NUMBER,
            module,
        )
        bank_rows = await self._async_rows(
            _as_int(extra[OID2_BANK_TABLE_SIZE]) or 0,
            OID2_BANK_MODULE,
            OID2_BANK_NUMBER,
            module,
        )
        # Phases first, then banks, as rPDU numbers its load rows
        loads = [
            LoadEntry(index=index, phase=number, row=row)
            for index, (number, row) in enumerate(sorted(phase_rows.items()), 1)
        ]
        loads += [
            LoadEntry(index=index, bank=number, row=row)
            for index, (number, row) in enumerate(sorted(bank_rows.items()), len(loads) + 1)
        ]
        has_voltage = False
        if phase_rows:
            first_phase = min(phase_rows.values())
            voltage = await self.async_get([f"{OID2_PHASE_VOLTAGE}.{first_phase}"])
            has_voltage = _non_negative(voltage[f"{OID2_PHASE_VOLTAGE}.{first_phase}"]) is not None
        return PDUInfo(
            model=model,
            serial=ident[f"{OID2_IDENT_SERIAL}.1"] or None,
            name=ident[f"{OID2_IDENT_NAME}.1"] or None,
            firmware=ident[f"{OID2_IDENT_FIRMWARE_REV}.1"] or None,
            hardware=ident[f"{OID2_IDENT_HARDWARE_REV}.1"] or None,
            outlet_count=len(outlet_rows),
            rated_current=_non_negative(extra[f"{OID2_DEVICE_MAX_CURRENT}.1"]) or None,
            has_power=_non_negative(extra[f"{OID2_DEVICE_POWER}.1"]) is not None,
            has_outlet_current=bool(metered_rows),
            has_voltage=has_voltage,
            has_energy=_non_negative(extra[f"{OID2_DEVICE_ENERGY}.1"]) is not None,
            loads=loads,
            mib=MIB_RPDU2,
            outlet_rows=outlet_rows,
            metered_rows=metered_rows,
        )

    async def _async_rows(
        self, size: int, module_oid: str, number_oid: str, module: int | None
    ) -> dict[int, int]:
        """Map outlet, phase or bank number to its table row, for one PDU."""
        if size < 1:
            return {}
        rows = range(1, size + 1)
        values = await self.async_get(
            [f"{oid}.{row}" for row in rows for oid in (module_oid, number_oid)]
        )
        numbers: dict[int, int] = {}
        for row in rows:
            if (number := _as_int(values[f"{number_oid}.{row}"])) is None:
                continue
            row_module = _as_int(values[f"{module_oid}.{row}"])
            if module is not None and row_module is not None and row_module != module:
                continue
            numbers.setdefault(number, row)
        return numbers

    async def _async_get_spdu_info(self) -> PDUInfo | None:
        ident = await self.async_get(
            [OIDS_MODEL, OIDS_SERIAL, OIDS_FIRMWARE_REV, OIDS_HARDWARE_REV, OIDS_OUTLET_COUNT]
        )
        outlet_count = _as_int(ident[OIDS_OUTLET_COUNT])
        if not ident[OIDS_MODEL] or not outlet_count or outlet_count < 1:
            _LOGGER.debug("%s has no sPDU MIB", self.host)
            return None
        return PDUInfo(
            model=ident[OIDS_MODEL],
            serial=ident[OIDS_SERIAL] or None,
            name=None,
            firmware=ident[OIDS_FIRMWARE_REV] or None,
            hardware=ident[OIDS_HARDWARE_REV] or None,
            outlet_count=outlet_count,
            mib=MIB_SPDU,
        )

    async def async_get_status(self, info: PDUInfo) -> PDUStatus:
        """Poll outlet states and load readings."""
        if info.mib == MIB_RPDU2:
            status = await self._async_get_rpdu2_status(info)
        elif info.mib == MIB_SPDU:
            status = await self._async_get_spdu_status(info)
        else:
            status = await self._async_get_rpdu_status(info)
        if all(outlet.is_on is None for outlet in status.outlets.values()):
            raise APCPDUError("The PDU did not report any outlet state")
        return status

    async def _async_get_rpdu_status(self, info: PDUInfo) -> PDUStatus:
        outlets = info.outlet_numbers
        oids = [f"{base}.{n}" for n in outlets for base in (OID_OUTLET_NAME, OID_OUTLET_STATE)]
        if info.has_outlet_current:
            oids += [f"{OID_OUTLET_CURRENT}.{n}" for n in outlets]
        for load in info.loads:
            oids += [f"{OID_LOAD_CURRENT}.{load.index}", f"{OID_LOAD_STATE}.{load.index}"]
        if info.has_power:
            oids.append(OID_POWER_WATTS)

        values = await self.async_get(oids)

        status = PDUStatus(outlets={})
        for n in outlets:
            status.outlets[n] = OutletStatus(
                name=values[f"{OID_OUTLET_NAME}.{n}"] or None,
                is_on=_switch_state(
                    values[f"{OID_OUTLET_STATE}.{n}"], OUTLET_STATE_ON, OUTLET_STATE_OFF
                ),
                current=(
                    _tenths(values[f"{OID_OUTLET_CURRENT}.{n}"])
                    if info.has_outlet_current
                    else None
                ),
            )
        for load in info.loads:
            status.load_current[load.index] = _tenths(values[f"{OID_LOAD_CURRENT}.{load.index}"])
            status.load_state[load.index] = LOAD_STATES.get(
                _as_int(values[f"{OID_LOAD_STATE}.{load.index}"])  # type: ignore[arg-type]
            )
        if info.has_power:
            status.power = _as_int(values[OID_POWER_WATTS])
        return status

    async def _async_get_rpdu2_status(self, info: PDUInfo) -> PDUStatus:
        oids = [
            f"{base}.{row}"
            for row in info.outlet_rows.values()
            for base in (OID2_OUTLET_NAME, OID2_OUTLET_STATE)
        ]
        oids += [f"{OID2_METERED_CURRENT}.{row}" for row in info.metered_rows.values()]
        for load in info.loads:
            if load.bank:
                oids += [f"{OID2_BANK_CURRENT}.{load.row}", f"{OID2_BANK_LOAD_STATE}.{load.row}"]
            else:
                oids += [f"{OID2_PHASE_CURRENT}.{load.row}", f"{OID2_PHASE_LOAD_STATE}.{load.row}"]
                if info.has_voltage:
                    oids.append(f"{OID2_PHASE_VOLTAGE}.{load.row}")
        if info.has_power:
            oids.append(f"{OID2_DEVICE_POWER}.1")
        if info.has_energy:
            oids.append(f"{OID2_DEVICE_ENERGY}.1")

        values = await self.async_get(oids)

        status = PDUStatus(outlets={})
        for n, row in info.outlet_rows.items():
            metered_row = info.metered_rows.get(n)
            status.outlets[n] = OutletStatus(
                name=values[f"{OID2_OUTLET_NAME}.{row}"] or None,
                is_on=_switch_state(
                    values[f"{OID2_OUTLET_STATE}.{row}"], OUTLET2_STATE_ON, OUTLET2_STATE_OFF
                ),
                current=(
                    _tenths(values[f"{OID2_METERED_CURRENT}.{metered_row}"])
                    if metered_row is not None
                    else None
                ),
            )
        for load in info.loads:
            current_oid, state_oid = (
                (OID2_BANK_CURRENT, OID2_BANK_LOAD_STATE)
                if load.bank
                else (OID2_PHASE_CURRENT, OID2_PHASE_LOAD_STATE)
            )
            status.load_current[load.index] = _tenths(values[f"{current_oid}.{load.row}"])
            status.load_state[load.index] = LOAD_STATES2.get(
                _as_int(values[f"{state_oid}.{load.row}"])  # type: ignore[arg-type]
            )
            if info.has_voltage and not load.bank:
                status.voltage[load.index] = _non_negative(
                    values[f"{OID2_PHASE_VOLTAGE}.{load.row}"]
                )
        if (
            info.has_power
            and (power := _non_negative(values[f"{OID2_DEVICE_POWER}.1"])) is not None
        ):
            status.power = power * 10  # hundredths of kW
        if (
            info.has_energy
            and (energy := _non_negative(values[f"{OID2_DEVICE_ENERGY}.1"])) is not None
        ):
            status.energy = energy / 10  # tenths of kWh
        return status

    async def _async_get_spdu_status(self, info: PDUInfo) -> PDUStatus:
        outlets = info.outlet_numbers
        values = await self.async_get(
            [f"{base}.{n}" for n in outlets for base in (OIDS_OUTLET_NAME, OIDS_OUTLET_CTL)]
        )
        return PDUStatus(
            outlets={
                n: OutletStatus(
                    name=values[f"{OIDS_OUTLET_NAME}.{n}"] or None,
                    is_on=_switch_state(
                        values[f"{OIDS_OUTLET_CTL}.{n}"], OUTLET_COMMAND_ON, OUTLET_COMMAND_OFF
                    ),
                )
                for n in outlets
            }
        )

    async def async_set_outlet(self, outlet: int, on: bool) -> None:
        """Switch one outlet immediately."""
        command = OUTLET_COMMAND_ON if on else OUTLET_COMMAND_OFF
        info = self._info
        if info is not None and info.mib == MIB_RPDU2:
            await self.async_set_int(f"{OID2_OUTLET_COMMAND}.{info.outlet_rows[outlet]}", command)
        elif info is not None and info.mib == MIB_SPDU:
            await self.async_set_int(f"{OIDS_OUTLET_CTL}.{outlet}", command)
        else:
            await self.async_set_int(f"{OID_OUTLET_COMMAND}.{outlet}", command)

    async def async_close(self) -> None:
        """Release the SNMP engine's sockets."""
        engine, self._engine, self._target = self._engine, None, None
        if engine is None:
            return
        try:
            if PYSNMP_7:
                engine.close_dispatcher()
            else:
                engine.closeDispatcher()
        except Exception:  # noqa: BLE001 - nothing useful to do on shutdown
            _LOGGER.debug("Error closing SNMP engine", exc_info=True)
