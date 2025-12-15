"""Support for Pulsar meters."""

from __future__ import annotations

from dataclasses import dataclass
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.device_registry import DeviceEntry
import homeassistant.helpers.entity_registry as er
from homeassistant.helpers.typing import ConfigType

from .const import (
    CONF_DEVICE_CONFIG,
    DATA_PULSAR,
    DATA_PULSAR_CONFIG,
    DOMAIN,
    PLATFORMS,
)
from .coordinator import PulsarDataUpdateCoordinator
from .pulsar_manager import PulsarManager

UNSUB_LISTENER = "unsub_listener"


@dataclass
class HomeAssistantPulsarData:
    """Runtime data for Pulsar integration."""

    device_manager: PulsarManager
    coordinators: dict[str, PulsarDataUpdateCoordinator]


type PulsarConfigEntry = ConfigEntry[HomeAssistantPulsarData]


# Internal definitions
_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up Pulsar from config."""
    hass.data[DATA_PULSAR] = {}

    if DOMAIN in config:
        conf = config[DOMAIN]
        hass.data[DATA_PULSAR][DATA_PULSAR_CONFIG] = conf

    return True


async def async_setup_entry(hass: HomeAssistant, entry: PulsarConfigEntry) -> bool:
    """Set up Pulsar with connection validation."""
    device_manager = PulsarManager(hass, entry)

    # Test connection before proceeding
    try:
        await hass.async_add_executor_job(device_manager.test_connection)
    except Exception as err:
        raise ConfigEntryNotReady(f"Unable to connect to serial device: {err}") from err

    # Create coordinator for each device
    coordinators: dict[str, PulsarDataUpdateCoordinator] = {}
    devices = device_manager.get_devices(None)

    for device_id, device in devices.items():
        coordinator = PulsarDataUpdateCoordinator(hass, device, device_id)
        await coordinator.async_config_entry_first_refresh()
        coordinators[device_id] = coordinator

    entry.runtime_data = HomeAssistantPulsarData(
        device_manager=device_manager, coordinators=coordinators
    )

    # Register devices in device registry
    device_registry = dr.async_get(hass)
    for device_id, device in devices.items():
        device_registry.async_get_or_create(
            config_entry_id=entry.entry_id,
            identifiers={(DOMAIN, device_id)},
            manufacturer="Pulsar",
            name=device.name,
            model=device.type,
        )

    entry.async_on_unload(entry.add_update_listener(async_update_listener))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_update_listener(hass: HomeAssistant, config_entry: ConfigEntry):
    """Update listener."""
    await hass.config_entries.async_reload(config_entry.entry_id)


async def async_remove_config_entry_device(
    hass: HomeAssistant, config_entry: PulsarConfigEntry, device_entry: DeviceEntry
) -> bool:
    """Remove a config entry from a device."""
    dev_id = next(iter(device_entry.identifiers))[1]
    ent_reg = er.async_get(hass)
    entities = {
        ent.unique_id: ent.entity_id
        for ent in er.async_entries_for_config_entry(ent_reg, config_entry.entry_id)
        if dev_id in ent.unique_id
    }
    for entity_id in entities.values():
        ent_reg.async_remove(entity_id)

    if dev_id not in config_entry.data[CONF_DEVICE_CONFIG]:
        _LOGGER.info(
            "Device %s not found in config entry: finalizing device removal", dev_id
        )
        return True

    new_data = config_entry.data.copy()
    new_data[CONF_DEVICE_CONFIG].pop(dev_id)

    hass.config_entries.async_update_entry(
        config_entry,
        data=new_data,
    )

    _LOGGER.info("Device %s removed.", dev_id)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: PulsarConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        # Clean up coordinators
        if entry.runtime_data:
            for coordinator in entry.runtime_data.coordinators.values():
                await coordinator.async_shutdown()

        # Clean up legacy hass.data if it exists
        if DOMAIN in hass.data and entry.entry_id in hass.data[DOMAIN]:
            hass.data[DOMAIN].pop(entry.entry_id)
            if not hass.config_entries.async_entries(DOMAIN):
                hass.data.pop(DOMAIN)

    return unload_ok
