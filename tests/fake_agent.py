"""A tiny SNMP v1/v2c agent that behaves like an APC Switched Rack PDU.

Used to exercise the real pysnmp client end to end on 127.0.0.1.
"""

from __future__ import annotations

import asyncio
from typing import Any

from pyasn1.codec.ber import decoder, encoder
from pysnmp.proto import api, rfc1905

_MODULES = getattr(api, "PROTOCOL_MODULES", None) or api.protoModules
_decode_version = getattr(api, "decode_message_version", None) or api.decodeMessageVersion

RPDU = "1.3.6.1.4.1.318.1.1.12"


def _call(obj: Any, snake: str, camel: str, *args: Any) -> Any:
    return getattr(obj, snake if hasattr(obj, snake) else camel)(*args)


def ap7920_values(outlets: int = 8) -> dict[str, Any]:
    """An AP7920: one phase, no per-outlet metering, no total power OID."""
    values: dict[str, Any] = {
        f"{RPDU}.1.1.0": "RackPDU",
        f"{RPDU}.1.2.0": "HW05",
        f"{RPDU}.1.3.0": "v3.7.3",
        f"{RPDU}.1.5.0": "AP7920",
        f"{RPDU}.1.6.0": "ZA0123456789",
        f"{RPDU}.1.7.0": 10,
        f"{RPDU}.1.8.0": outlets,
        f"{RPDU}.1.15.0": 230,
        f"{RPDU}.1.17.0": 1000,
        f"{RPDU}.2.1.2.0": 1,
        f"{RPDU}.2.1.4.0": 0,
        f"{RPDU}.2.3.1.1.2.1": 17,
        f"{RPDU}.2.3.1.1.3.1": 1,
        f"{RPDU}.2.3.1.1.4.1": 1,
        f"{RPDU}.2.3.1.1.5.1": 0,
    }
    for n in range(1, outlets + 1):
        values[f"{RPDU}.3.3.1.1.4.{n}"] = 1 if n % 2 else 2
        values[f"{RPDU}.3.5.1.1.2.{n}"] = f"Outlet {n}"
        values[f"{RPDU}.3.5.1.1.4.{n}"] = 1 if n % 2 else 2
    return values


class FakeAPCAgent(asyncio.DatagramProtocol):
    """Answers GET/SET for a dict of OID -> value."""

    def __init__(
        self,
        values: dict[str, Any],
        read_community: str = "public",
        write_community: str = "private",
    ) -> None:
        self.values = values
        self.read_community = read_community
        self.write_community = write_community
        self.requests = 0
        self.transport: asyncio.DatagramTransport | None = None
        self.port = 0

    async def start(self) -> None:
        loop = asyncio.get_running_loop()
        self.transport, _ = await loop.create_datagram_endpoint(
            lambda: self, local_addr=("127.0.0.1", 0)
        )
        self.port = self.transport.get_extra_info("sockname")[1]

    def stop(self) -> None:
        if self.transport:
            self.transport.close()

    def datagram_received(self, data: bytes, addr: Any) -> None:
        response = self._handle(data)
        if response is not None and self.transport:
            self.transport.sendto(response, addr)

    def _handle(self, data: bytes) -> bytes | None:
        version = int(_decode_version(data))
        if version not in _MODULES:
            return None  # SNMPv3 is not emulated
        proto = _MODULES[version]
        msg_api, pdu_api = proto.apiMessage, proto.apiPDU
        message, _ = decoder.decode(data, asn1Spec=proto.Message())
        community = str(_call(msg_api, "get_community", "getCommunity", message))
        if community not in (self.read_community, self.write_community):
            return None  # real agents silently drop bad communities
        self.requests += 1
        request = _call(msg_api, "get_pdu", "getPDU", message)
        response_msg = _call(msg_api, "get_response", "getResponse", message)
        response = _call(msg_api, "get_pdu", "getPDU", response_msg)
        var_binds = _call(pdu_api, "get_varbinds", "getVarBinds", request)

        status, index, out = 0, 0, []
        if request.tagSet == proto.GetRequestPDU.tagSet:
            for i, (oid, _) in enumerate(var_binds, 1):
                key = str(oid.prettyPrint())
                if key in self.values:
                    value = self.values[key]
                    out.append(
                        (
                            oid,
                            proto.OctetString(value)
                            if isinstance(value, str)
                            else proto.Integer(value),
                        )
                    )
                elif version == 0:
                    status, index, out = 2, i, list(var_binds)  # noSuchName
                    break
                else:
                    out.append((oid, rfc1905.noSuchInstance))
        elif request.tagSet == proto.SetRequestPDU.tagSet:
            if community != self.write_community:
                status, index, out = (2 if version == 0 else 6), 1, list(var_binds)
            else:
                for oid, value in var_binds:
                    key = str(oid.prettyPrint())
                    if key.startswith(f"{RPDU}.3.3.1.1.4."):
                        outlet = key.rsplit(".", 1)[1]
                        self.values[key] = int(value)
                        self.values[f"{RPDU}.3.5.1.1.4.{outlet}"] = int(value)
                    else:
                        self.values[key] = value
                    out.append((oid, value))
        else:
            return None

        _call(pdu_api, "set_error_status", "setErrorStatus", response, status)
        _call(pdu_api, "set_error_index", "setErrorIndex", response, index)
        _call(pdu_api, "set_varbinds", "setVarBinds", response, out)
        return encoder.encode(response_msg)


def _name(obj: Any, snake: str, camel: str) -> Any:
    return getattr(obj, snake if hasattr(obj, snake) else camel)


def start_v3_agent(
    values: dict[str, Any], user: str, auth_key: str, priv_key: str
) -> tuple[Any, int]:
    """Start an SNMPv3 (SHA/AES) agent using pysnmp's own command responder.

    Returns the engine (close it with close_v3_agent) and the UDP port.
    """
    import socket  # noqa: PLC0415

    from pysnmp.carrier.asyncio.dgram import udp  # noqa: PLC0415
    from pysnmp.entity import config, engine  # noqa: PLC0415
    from pysnmp.entity.rfc3413 import cmdrsp, context  # noqa: PLC0415
    from pysnmp.proto.api import v2c  # noqa: PLC0415

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]

    snmp_engine = engine.SnmpEngine()
    transport = _name(udp.UdpAsyncioTransport(), "open_server_mode", "openServerMode")(
        ("127.0.0.1", port)
    )
    domain = getattr(udp, "DOMAIN_NAME", None) or udp.domainName
    _name(config, "add_transport", "addTransport")(snmp_engine, domain, transport)
    _name(config, "add_v3_user", "addV3User")(
        snmp_engine,
        user,
        getattr(config, "USM_AUTH_HMAC96_SHA", None) or config.usmHMACSHAAuthProtocol,
        auth_key,
        getattr(config, "USM_PRIV_CFB128_AES", None) or config.usmAesCfb128Protocol,
        priv_key,
    )
    _name(config, "add_vacm_user", "addVacmUser")(
        snmp_engine, 3, user, "authPriv", (1, 3, 6), (1, 3, 6)
    )
    snmp_context = context.SnmpContext(snmp_engine)
    builder = _name(
        _name(snmp_context, "get_mib_instrum", "getMibInstrum")(),
        "get_mib_builder",
        "getMibBuilder",
    )()
    scalar, instance = _name(builder, "import_symbols", "importSymbols")(
        "SNMPv2-SMI", "MibScalar", "MibScalarInstance"
    )
    symbols = {}
    for i, (oid, value) in enumerate(values.items()):
        parts = tuple(int(part) for part in oid.split("."))
        typed = v2c.OctetString(value) if isinstance(value, str) else v2c.Integer(value)
        symbols[f"scalar{i}"] = scalar(parts[:-1], typed.clone())
        symbols[f"instance{i}"] = instance(parts[:-1], (parts[-1],), typed)
    _name(builder, "export_symbols", "exportSymbols")("FAKE-APC-MIB", **symbols)
    cmdrsp.GetCommandResponder(snmp_engine, snmp_context)
    dispatcher = _name(snmp_engine, "transport_dispatcher", "transportDispatcher")
    _name(dispatcher, "job_started", "jobStarted")(1)
    return snmp_engine, port


def close_v3_agent(snmp_engine: Any) -> None:
    """Stop an agent started with start_v3_agent."""
    _name(snmp_engine, "close_dispatcher", "closeDispatcher")()
