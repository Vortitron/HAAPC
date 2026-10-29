"""Config flow for APC PDU."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import (
    SOURCE_RECONFIGURE,
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
)
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_SCAN_INTERVAL, CONF_USERNAME
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .const import (
    AUTH_NONE,
    AUTH_PROTOCOLS,
    CONF_AUTH_KEY,
    CONF_AUTH_PROTOCOL,
    CONF_COMMUNITY,
    CONF_PRIV_KEY,
    CONF_PRIV_PROTOCOL,
    CONF_SNMP_VERSION,
    DEFAULT_COMMUNITY,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SNMP_VERSION,
    DOMAIN,
    MAX_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
    PRIV_NONE,
    PRIV_PROTOCOLS,
    SNMP_VERSION_3,
    SNMP_VERSIONS,
)
from .coordinator import client_from_data
from .snmp import APCPDUError, CannotConnect, InvalidAuth, NotSupported, PDUInfo

try:  # Home Assistant 2025.8+ reloads the entry itself after the options flow
    from homeassistant.config_entries import OptionsFlowWithReload as _OptionsFlow

    OPTIONS_FLOW_RELOADS = True
except ImportError:  # older releases: __init__ applies options via an update listener
    from homeassistant.config_entries import OptionsFlow as _OptionsFlow

    OPTIONS_FLOW_RELOADS = False

_LOGGER = logging.getLogger(__name__)

MIN_KEY_LENGTH = 8  # RFC 3414 minimum for SNMPv3 passphrases

_PASSWORD = TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD))


def _select(options: list[str], key: str) -> SelectSelector:
    return SelectSelector(
        SelectSelectorConfig(options=options, translation_key=key, mode=SelectSelectorMode.DROPDOWN)
    )


def _connection_schema(defaults: Mapping[str, Any]) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_HOST, default=defaults.get(CONF_HOST, vol.UNDEFINED)): str,
            vol.Required(
                CONF_COMMUNITY, default=defaults.get(CONF_COMMUNITY) or DEFAULT_COMMUNITY
            ): _PASSWORD,
            vol.Required(
                CONF_SNMP_VERSION,
                default=defaults.get(CONF_SNMP_VERSION, DEFAULT_SNMP_VERSION),
            ): _select(SNMP_VERSIONS, CONF_SNMP_VERSION),
            vol.Required(CONF_PORT, default=defaults.get(CONF_PORT, DEFAULT_PORT)): vol.All(
                vol.Coerce(int), vol.Range(min=1, max=65535)
            ),
        }
    )


def _snmpv3_schema(defaults: Mapping[str, Any]) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_USERNAME, default=defaults.get(CONF_USERNAME, vol.UNDEFINED)): str,
            vol.Required(
                CONF_AUTH_PROTOCOL, default=defaults.get(CONF_AUTH_PROTOCOL, "sha")
            ): _select(AUTH_PROTOCOLS, CONF_AUTH_PROTOCOL),
            vol.Optional(CONF_AUTH_KEY, default=defaults.get(CONF_AUTH_KEY, "")): _PASSWORD,
            vol.Required(
                CONF_PRIV_PROTOCOL, default=defaults.get(CONF_PRIV_PROTOCOL, "aes")
            ): _select(PRIV_PROTOCOLS, CONF_PRIV_PROTOCOL),
            vol.Optional(CONF_PRIV_KEY, default=defaults.get(CONF_PRIV_KEY, "")): _PASSWORD,
        }
    )


def _snmpv3_errors(data: Mapping[str, Any]) -> dict[str, str]:
    errors: dict[str, str] = {}
    auth = data.get(CONF_AUTH_PROTOCOL, AUTH_NONE)
    priv = data.get(CONF_PRIV_PROTOCOL, PRIV_NONE)
    if auth != AUTH_NONE and len(data.get(CONF_AUTH_KEY) or "") < MIN_KEY_LENGTH:
        errors[CONF_AUTH_KEY] = "key_too_short"
    if priv != PRIV_NONE:
        if auth == AUTH_NONE:
            errors["base"] = "priv_requires_auth"
        elif len(data.get(CONF_PRIV_KEY) or "") < MIN_KEY_LENGTH:
            errors[CONF_PRIV_KEY] = "key_too_short"
    return errors


async def _async_probe(data: dict[str, Any]) -> tuple[PDUInfo | None, str | None]:
    """Read the PDU's identity; return (info, error key)."""
    client = client_from_data(data)
    try:
        return await client.async_get_info(), None
    except InvalidAuth:
        return None, "invalid_auth"
    except NotSupported as err:
        _LOGGER.debug("Not a supported APC PDU: %s", err)
        return None, "not_supported"
    except (CannotConnect, APCPDUError) as err:
        _LOGGER.debug("Cannot read %s: %s", data.get(CONF_HOST), err)
        return None, "cannot_connect"
    except Exception:
        _LOGGER.exception("Unexpected error talking to %s", data.get(CONF_HOST))
        return None, "unknown"
    finally:
        await client.async_close()


class APCPDUConfigFlow(ConfigFlow, domain=DOMAIN):
    """Set up an APC PDU."""

    VERSION = 1
    MINOR_VERSION = 2

    def __init__(self) -> None:
        """Initialise the flow."""
        self._data: dict[str, Any] = {}

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> APCPDUOptionsFlow:
        """Return the options flow."""
        return APCPDUOptionsFlow()

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Ask where the PDU is and how to reach it."""
        return await self._async_step_connection("user", user_input, {})

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Change the address or credentials of an existing PDU."""
        return await self._async_step_connection(
            "reconfigure", user_input, self._get_reconfigure_entry().data
        )

    async def _async_step_connection(
        self,
        step_id: str,
        user_input: dict[str, Any] | None,
        defaults: Mapping[str, Any],
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            user_input[CONF_HOST] = user_input[CONF_HOST].strip()
            if user_input[CONF_SNMP_VERSION] == SNMP_VERSION_3:
                user_input.pop(CONF_COMMUNITY, None)
                self._data = user_input
                return await self.async_step_snmpv3()
            result = await self._async_validate_and_finish(user_input, errors)
            if result is not None:
                return result
            defaults = user_input
        return self.async_show_form(
            step_id=step_id, data_schema=_connection_schema(defaults), errors=errors
        )

    async def async_step_snmpv3(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Ask for SNMPv3 credentials."""
        errors: dict[str, str] = {}
        defaults: Mapping[str, Any] = {}
        if self.source == SOURCE_RECONFIGURE:
            defaults = self._get_reconfigure_entry().data
        if user_input is not None:
            errors = _snmpv3_errors(user_input)
            if not errors:
                data = {**self._data, **user_input}
                if data[CONF_AUTH_PROTOCOL] == AUTH_NONE:
                    data.pop(CONF_AUTH_KEY, None)
                if data[CONF_PRIV_PROTOCOL] == PRIV_NONE:
                    data.pop(CONF_PRIV_KEY, None)
                result = await self._async_validate_and_finish(data, errors)
                if result is not None:
                    return result
            defaults = user_input
        return self.async_show_form(
            step_id="snmpv3",
            data_schema=_snmpv3_schema(defaults),
            errors=errors,
            description_placeholders={"host": self._data.get(CONF_HOST, "")},
        )

    async def _async_validate_and_finish(
        self, data: dict[str, Any], errors: dict[str, str]
    ) -> ConfigFlowResult | None:
        """Probe the PDU, then create or update the entry; None on error."""
        info, error = await _async_probe(data)
        if info is None:
            errors["base"] = error or "unknown"
            return None

        if self.source == SOURCE_RECONFIGURE:
            entry = self._get_reconfigure_entry()
            if entry.unique_id and info.serial:
                await self.async_set_unique_id(info.serial)
                self._abort_if_unique_id_mismatch(reason="wrong_device")
            return self.async_update_reload_and_abort(entry, data=data)

        if info.serial:
            await self.async_set_unique_id(info.serial)
            # The same PDU at a new address updates the existing entry
            self._abort_if_unique_id_configured(updates=data)
        else:
            self._async_abort_entries_match({CONF_HOST: data[CONF_HOST]})
        return self.async_create_entry(title=info.name or info.model or "APC PDU", data=data)


class APCPDUOptionsFlow(_OptionsFlow):
    """Polling options."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Choose how often the PDU is polled."""
        if user_input is not None:
            return self.async_create_entry(
                data={CONF_SCAN_INTERVAL: int(user_input[CONF_SCAN_INTERVAL])}
            )
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_SCAN_INTERVAL,
                        default=self.config_entry.options.get(
                            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                        ),
                    ): NumberSelector(
                        NumberSelectorConfig(
                            min=MIN_SCAN_INTERVAL,
                            max=MAX_SCAN_INTERVAL,
                            step=1,
                            unit_of_measurement="s",
                            mode=NumberSelectorMode.BOX,
                        )
                    ),
                }
            ),
        )
