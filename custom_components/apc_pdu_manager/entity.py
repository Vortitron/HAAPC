"""Base entity for APC PDU."""

from __future__ import annotations

from homeassistant.const import CONF_HOST
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER
from .coordinator import APCPDUCoordinator


class APCPDUEntity(CoordinatorEntity[APCPDUCoordinator]):
    """An entity belonging to one PDU device."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: APCPDUCoordinator, key: str) -> None:
        """Initialise the entity; key makes the unique ID."""
        super().__init__(coordinator)
        entry = coordinator.config_entry
        # The serial number when the PDU reports one, as in 1.0.x
        base = entry.unique_id or entry.entry_id
        self._attr_unique_id = f"{base}_{key}"
        host = entry.data[CONF_HOST]
        if ":" in host and not host.startswith("["):
            host = f"[{host}]"
        info = coordinator.info
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, base)},
            name=entry.title,
            manufacturer=MANUFACTURER,
            model=info.model,
            serial_number=info.serial,
            sw_version=info.firmware,
            hw_version=info.hardware,
            configuration_url=f"http://{host}",
        )
