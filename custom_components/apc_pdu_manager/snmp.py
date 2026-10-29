"""Async SNMP client for APC Switched Rack PDUs (PowerNet-MIB rPDU branch)."""

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
    """The device answered but does not look like an APC Switched Rack PDU."""


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
    loads: list[LoadEntry] = field(default_factory=list)


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
    power: int | None = None


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
        """Identify the PDU and work out which optional values it provides."""
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
            raise NotSupported(
                f"{self.host} answered but does not expose the APC rPDU MIB "
                f"(model={ident[OID_MODEL]!r}, outlets={ident[OID_OUTLET_COUNT]!r})"
            )
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

    async def async_get_status(self, info: PDUInfo) -> PDUStatus:
        """Poll outlet states and load readings."""
        outlets = range(1, info.outlet_count + 1)
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
            state = _as_int(values[f"{OID_OUTLET_STATE}.{n}"])
            status.outlets[n] = OutletStatus(
                name=values[f"{OID_OUTLET_NAME}.{n}"] or None,
                is_on=(
                    True
                    if state == OUTLET_STATE_ON
                    else False
                    if state == OUTLET_STATE_OFF
                    else None
                ),
                current=(
                    _tenths(values[f"{OID_OUTLET_CURRENT}.{n}"])
                    if info.has_outlet_current
                    else None
                ),
            )
        if all(outlet.is_on is None for outlet in status.outlets.values()):
            raise APCPDUError("The PDU did not report any outlet state")
        for load in info.loads:
            status.load_current[load.index] = _tenths(values[f"{OID_LOAD_CURRENT}.{load.index}"])
            status.load_state[load.index] = LOAD_STATES.get(
                _as_int(values[f"{OID_LOAD_STATE}.{load.index}"])  # type: ignore[arg-type]
            )
        if info.has_power:
            status.power = _as_int(values[OID_POWER_WATTS])
        return status

    async def async_set_outlet(self, outlet: int, on: bool) -> None:
        """Switch one outlet immediately."""
        await self.async_set_int(
            f"{OID_OUTLET_COMMAND}.{outlet}", OUTLET_COMMAND_ON if on else OUTLET_COMMAND_OFF
        )

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
