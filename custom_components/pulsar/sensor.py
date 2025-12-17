"""Support for Pulsar devices."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    EntityCategory,
    UnitOfElectricPotential,
    UnitOfTemperature,
    UnitOfVolume,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import HomeAssistantPulsarData, PulsarConfigEntry
from .const import (
    DATA_KEY_BATTERY_VOLTAGE,
    DATA_KEY_CURRENT_WATER_CONSUMPTION_CH1,
    DATA_KEY_DEVICE_TEMPERATURE,
    DATA_KEY_ERROR_FLAGS,
    DATA_KEY_SYSTEM_TIME,
    DOMAIN,
    PULSAR_DISCOVERY_NEW,
)
from .coordinator import PulsarDataUpdateCoordinator


@dataclass(frozen=True)
class PulsarSensorEntityDescription(SensorEntityDescription):
    """Describes Pulsar sensor entity."""

    subkey: str | None = None


SENSORS: dict[str, tuple[PulsarSensorEntityDescription, ...]] = {
    "pulsar-m-water": (
        PulsarSensorEntityDescription(
            key=DATA_KEY_CURRENT_WATER_CONSUMPTION_CH1,
            translation_key=DATA_KEY_CURRENT_WATER_CONSUMPTION_CH1,
            device_class=SensorDeviceClass.WATER,
            state_class=SensorStateClass.TOTAL_INCREASING,
            native_unit_of_measurement=UnitOfVolume.LITERS,
            suggested_display_precision=0,
            has_entity_name=True,
        ),
        PulsarSensorEntityDescription(
            key=DATA_KEY_SYSTEM_TIME,
            translation_key=DATA_KEY_SYSTEM_TIME,
            entity_category=EntityCategory.DIAGNOSTIC,
            icon="mdi:clock",
            has_entity_name=True,
        ),
        PulsarSensorEntityDescription(
            key=DATA_KEY_DEVICE_TEMPERATURE,
            translation_key=DATA_KEY_DEVICE_TEMPERATURE,
            device_class=SensorDeviceClass.TEMPERATURE,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
            suggested_display_precision=1,
            has_entity_name=True,
        ),
        PulsarSensorEntityDescription(
            key=DATA_KEY_BATTERY_VOLTAGE,
            translation_key=DATA_KEY_BATTERY_VOLTAGE,
            device_class=SensorDeviceClass.VOLTAGE,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement=UnitOfElectricPotential.VOLT,
            suggested_display_precision=1,
            has_entity_name=True,
        ),
        PulsarSensorEntityDescription(
            key=DATA_KEY_ERROR_FLAGS,
            translation_key=DATA_KEY_ERROR_FLAGS,
            device_class=None,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement=None,
            entity_category=EntityCategory.DIAGNOSTIC,
            icon="mdi:alert-circle",
            has_entity_name=True,
        ),
    )
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: PulsarConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Pulsar sensor dynamically."""
    hass_data: HomeAssistantPulsarData = entry.runtime_data

    @callback
    def async_discover_device(device_ids: list[str]) -> None:
        """Discover and add a discovered Pulsar sensor."""
        entities: list[PulsarSensorEntity] = []
        for device_id in device_ids:
            coordinator = hass_data.coordinators.get(device_id)
            if coordinator is None:
                continue
            device = coordinator.device
            if descriptions := SENSORS.get(device.type):
                entities.extend(
                    PulsarSensorEntity(coordinator, device_id, description)
                    for description in descriptions
                )

        async_add_entities(entities)

    async_discover_device([*hass_data.coordinators.keys()])

    entry.async_on_unload(
        async_dispatcher_connect(hass, PULSAR_DISCOVERY_NEW, async_discover_device)
    )


class PulsarSensorEntity(CoordinatorEntity[PulsarDataUpdateCoordinator], SensorEntity):
    """Pulsar Sensor Entity using coordinator."""

    def __init__(
        self,
        coordinator: PulsarDataUpdateCoordinator,
        device_id: str,
        description: PulsarSensorEntityDescription,
    ) -> None:
        """Initialize Pulsar sensor entity."""
        super().__init__(coordinator)
        self.entity_description = description
        self._device_id = device_id
        self._attr_unique_id = f"pulsar.{device_id}.{description.key}"

    @property
    def available(self) -> bool:  # type: ignore[override]
        """Return if entity is available."""
        return self.coordinator.last_update_success

    @property
    def native_value(self) -> StateType:  # type: ignore[override]
        """Return the value reported by the sensor."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get(self.entity_description.key)

    @property
    def device_info(self) -> DeviceInfo:  # type: ignore[override]
        """Return device information."""
        device = self.coordinator.device
        sw_version = self.coordinator.firmware_version

        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            manufacturer="Pulsar",
            model=device.type,
            name=device.name,
            sw_version=str(sw_version) if sw_version is not None else None,
            serial_number=str(device.serial_number),
        )
