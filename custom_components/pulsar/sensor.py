"""Support for Pulsar devices."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import UnitOfTemperature, UnitOfVolume
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import HomeAssistantPulsarData, PulsarConfigEntry
from .const import (
    DATA_KEY_CURRENT_WATER_CONSUMPTION_CH1,
    DATA_KEY_DEVICE_TEMPERATURE,
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
            name="Current water consumption",
            translation_key=DATA_KEY_CURRENT_WATER_CONSUMPTION_CH1,
            device_class=SensorDeviceClass.WATER,
            state_class=SensorStateClass.TOTAL_INCREASING,
            native_unit_of_measurement=UnitOfVolume.LITERS,
            has_entity_name=True,
        ),
        PulsarSensorEntityDescription(
            key=DATA_KEY_SYSTEM_TIME,
            name="System time",
            translation_key=DATA_KEY_SYSTEM_TIME,
            has_entity_name=True,
        ),
        PulsarSensorEntityDescription(
            key=DATA_KEY_DEVICE_TEMPERATURE,
            name="Temperature of meter",
            translation_key=DATA_KEY_DEVICE_TEMPERATURE,
            device_class=SensorDeviceClass.TEMPERATURE,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
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
        self._attr_name = None  # Use has_entity_name

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
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            manufacturer="Pulsar",
            model=self.coordinator.device.type,
            name=self.coordinator.device.name,
        )
