"""Outlet switches for APC PDU."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import APCPDUConfigEntry, APCPDUCoordinator
from .entity import APCPDUEntity
from .snmp import APCPDUError

PARALLEL_UPDATES = 1


async def async_setup_entry(
    hass: HomeAssistant,
    entry: APCPDUConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Create one switch per outlet plus one for all outlets."""
    coordinator = entry.runtime_data
    entities: list[SwitchEntity] = [
        APCPDUOutletSwitch(coordinator, outlet) for outlet in coordinator.info.outlet_numbers
    ]
    entities.append(APCPDUAllOutletsSwitch(coordinator))
    async_add_entities(entities)


def _command_error(target: str, err: APCPDUError) -> HomeAssistantError:
    return HomeAssistantError(
        translation_domain=DOMAIN,
        translation_key="command_failed",
        translation_placeholders={"target": target, "error": str(err) or type(err).__name__},
    )


class APCPDUOutletSwitch(APCPDUEntity, SwitchEntity):
    """One switched outlet."""

    _attr_device_class = SwitchDeviceClass.OUTLET

    def __init__(self, coordinator: APCPDUCoordinator, outlet: int) -> None:
        """Initialise the outlet switch."""
        super().__init__(coordinator, f"outlet_{outlet}")
        self.outlet = outlet
        self._attr_extra_state_attributes = {"outlet_number": outlet}

    @property
    def name(self) -> str:
        """Use the outlet name configured on the PDU."""
        status = self.coordinator.data.outlets.get(self.outlet)
        return (status.name if status else None) or f"Outlet {self.outlet}"

    @property
    def available(self) -> bool:
        """Unavailable when the PDU stops reporting this outlet."""
        status = self.coordinator.data.outlets.get(self.outlet)
        return super().available and status is not None and status.is_on is not None

    @property
    def is_on(self) -> bool | None:
        """Return whether the outlet is powered."""
        status = self.coordinator.data.outlets.get(self.outlet)
        return status.is_on if status else None

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Power the outlet on."""
        await self._async_switch(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Power the outlet off."""
        await self._async_switch(False)

    async def _async_switch(self, on: bool) -> None:
        try:
            await self.coordinator.client.async_set_outlet(self.outlet, on)
        except APCPDUError as err:
            raise _command_error(self.name, err) from err
        self.coordinator.data.outlets[self.outlet].is_on = on
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()


class APCPDUAllOutletsSwitch(APCPDUEntity, SwitchEntity):
    """Switches every outlet; on while any outlet is on."""

    _attr_translation_key = "all_outlets"

    def __init__(self, coordinator: APCPDUCoordinator) -> None:
        """Initialise the switch (unique ID kept from 1.0.x)."""
        super().__init__(coordinator, "master_switch")

    @property
    def is_on(self) -> bool:
        """Return True while any outlet is on."""
        return any(status.is_on for status in self.coordinator.data.outlets.values())

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Report how many outlets are on."""
        outlets = self.coordinator.data.outlets
        return {
            "total_outlets": len(outlets),
            "outlets_on": sum(1 for status in outlets.values() if status.is_on),
        }

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn every outlet on."""
        await self._async_switch_all(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn every outlet off."""
        await self._async_switch_all(False)

    async def _async_switch_all(self, on: bool) -> None:
        failed: list[str] = []
        error: APCPDUError | None = None
        for outlet, status in self.coordinator.data.outlets.items():
            try:
                await self.coordinator.client.async_set_outlet(outlet, on)
            except APCPDUError as err:
                failed.append(str(outlet))
                error = err
            else:
                status.is_on = on
        self.coordinator.async_update_listeners()
        await self.coordinator.async_request_refresh()
        if error is not None:
            raise _command_error(f"outlets {', '.join(failed)}", error) from error
