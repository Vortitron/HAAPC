"""Sensors for APC PDU."""

from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import (
    EntityCategory,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfPower,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import LOAD_STATES
from .coordinator import APCPDUConfigEntry, APCPDUCoordinator
from .entity import APCPDUEntity
from .snmp import LoadEntry

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: APCPDUConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Create sensors for the values this PDU actually reports."""
    coordinator = entry.runtime_data
    info = coordinator.info
    entities: list[SensorEntity] = []

    single = len(info.loads) == 1
    for load in info.loads:
        entities.append(APCPDULoadCurrentSensor(coordinator, load, single))
        entities.append(APCPDULoadStateSensor(coordinator, load, single))
    if info.has_power:
        entities.append(APCPDUPowerSensor(coordinator))
    if info.has_outlet_current:
        entities.extend(
            APCPDUOutletCurrentSensor(coordinator, outlet)
            for outlet in range(1, info.outlet_count + 1)
        )
    if info.rated_current:
        entities.append(
            APCPDURatingSensor(
                coordinator,
                "rated_current",
                info.rated_current,
                SensorDeviceClass.CURRENT,
                UnitOfElectricCurrent.AMPERE,
            )
        )
    if info.nominal_voltage:
        entities.append(
            APCPDURatingSensor(
                coordinator,
                # unique ID kept from 1.0.x ("Rated voltage")
                "rated_voltage",
                info.nominal_voltage,
                SensorDeviceClass.VOLTAGE,
                UnitOfElectricPotential.VOLT,
                translation_key="nominal_voltage",
            )
        )
    async_add_entities(entities)


def _load_translation(load: LoadEntry, single: bool, suffix: str) -> tuple[str, dict[str, str]]:
    """Name a phase/bank row: no prefix when the PDU has only one."""
    if single:
        return suffix, {}
    if load.bank:
        return f"bank_{suffix}", {"number": str(load.bank)}
    return f"phase_{suffix}", {"number": str(load.phase or load.index)}


class APCPDULoadCurrentSensor(APCPDUEntity, SensorEntity):
    """Measured current of a phase or bank."""

    _attr_device_class = SensorDeviceClass.CURRENT
    _attr_native_unit_of_measurement = UnitOfElectricCurrent.AMPERE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 1

    def __init__(self, coordinator: APCPDUCoordinator, load: LoadEntry, single: bool) -> None:
        """Initialise the sensor."""
        super().__init__(coordinator, f"load_{load.index}_current")
        self._index = load.index
        self._attr_translation_key, self._attr_translation_placeholders = _load_translation(
            load, single, "current"
        )

    @property
    def native_value(self) -> float | None:
        """Return the current in amps."""
        return self.coordinator.data.load_current.get(self._index)


class APCPDULoadStateSensor(APCPDUEntity, SensorEntity):
    """Load alarm state of a phase or bank."""

    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = list(LOAD_STATES.values())

    def __init__(self, coordinator: APCPDUCoordinator, load: LoadEntry, single: bool) -> None:
        """Initialise the sensor (row 1 keeps the 1.0.x unique ID)."""
        key = "bank_load_state" if load.index == 1 else f"load_{load.index}_state"
        super().__init__(coordinator, key)
        self._index = load.index
        self._attr_translation_key, self._attr_translation_placeholders = _load_translation(
            load, single, "load_state"
        )

    @property
    def native_value(self) -> str | None:
        """Return normal, low, near_overload or overload."""
        return self.coordinator.data.load_state.get(self._index)


class APCPDUPowerSensor(APCPDUEntity, SensorEntity):
    """Total power reported by the PDU."""

    _attr_device_class = SensorDeviceClass.POWER
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: APCPDUCoordinator) -> None:
        """Initialise the sensor."""
        super().__init__(coordinator, "power")
        self._attr_translation_key = "power"

    @property
    def native_value(self) -> int | None:
        """Return the power in watts."""
        return self.coordinator.data.power


class APCPDUOutletCurrentSensor(APCPDUEntity, SensorEntity):
    """Current drawn by one outlet (outlet-metered PDUs only)."""

    _attr_device_class = SensorDeviceClass.CURRENT
    _attr_native_unit_of_measurement = UnitOfElectricCurrent.AMPERE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 1

    def __init__(self, coordinator: APCPDUCoordinator, outlet: int) -> None:
        """Initialise the sensor."""
        super().__init__(coordinator, f"outlet_{outlet}_current")
        self.outlet = outlet

    @property
    def name(self) -> str:
        """Name after the outlet as configured on the PDU."""
        status = self.coordinator.data.outlets.get(self.outlet)
        return f"{(status.name if status else None) or f'Outlet {self.outlet}'} current"

    @property
    def native_value(self) -> float | None:
        """Return the current in amps."""
        status = self.coordinator.data.outlets.get(self.outlet)
        return status.current if status else None


class APCPDURatingSensor(APCPDUEntity, SensorEntity):
    """A fixed rating read from the PDU at setup."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        coordinator: APCPDUCoordinator,
        key: str,
        value: int,
        device_class: SensorDeviceClass,
        unit: str,
        translation_key: str | None = None,
    ) -> None:
        """Initialise the sensor."""
        super().__init__(coordinator, key)
        self._attr_translation_key = translation_key or key
        self._attr_native_value = value
        self._attr_device_class = device_class
        self._attr_native_unit_of_measurement = unit
