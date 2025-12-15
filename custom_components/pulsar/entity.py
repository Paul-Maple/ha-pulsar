"""Entity for Pulsar devices."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from functools import cached_property
import logging
from typing import Any

from homeassistant.core import callback
from homeassistant.helpers import entity
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN
from .pulsar_m_water import PulsarM
from .pulsardevice import PulsarDevice

_LOGGER = logging.getLogger(__name__)


class BasePulsarEntity(entity.Entity):
    """Base entity for Pulsar devices."""

    def __init__(
        self, unique_id: str, pulsar_device: PulsarDevice, **_kwargs: Any
    ) -> None:
        """Init Pulsar entity."""
        self._attr_unique_id = f"pulsar.{unique_id}"
        self._unique_id = unique_id
        self._name: str = pulsar_device.name
        self._state: Any = None
        self._attr_should_poll = True
        self._extra_state_attributes: dict[str, Any] = {}
        self._pulsar_device = pulsar_device
        self._unsubs: list[Callable[[], None]] = []
        self.remove_future: asyncio.Future[Any] = asyncio.Future()

    @property
    def pulsar_device(self) -> PulsarDevice:
        """Return the Pulsar device this entity is attached to."""
        return self._pulsar_device

    @cached_property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return device specific state attributes."""
        return self._extra_state_attributes

    @cached_property
    def device_info(self) -> DeviceInfo:
        """Return a device description for device registry."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._unique_id)},
            manufacturer="Pulsar",
            model=self._pulsar_device.type,
            name=self._pulsar_device.name,
        )

    @callback
    def async_state_changed(self) -> None:
        """Entity state changed."""
        self.async_write_ha_state()

    @callback
    def async_update_state_attribute(self, key: str, value: Any) -> None:
        """Update a single device state attribute."""
        self._extra_state_attributes.update({key: value})
        self.async_write_ha_state()

    @callback
    def async_set_state(self, attr_id: int, attr_name: str, value: Any) -> None:
        """Set the entity state."""

    async def async_will_remove_from_hass(self) -> None:
        """Disconnect entity object when removed."""
        for unsub in self._unsubs[:]:
            unsub()
            self._unsubs.remove(unsub)

    def log(self, level: int, msg: str, *args, **kwargs):
        """Log a message."""
        msg = f"%s: {msg}"
        _LOGGER.log(level, msg, self.entity_id, *args, **kwargs)


class PulsarMEntity(BasePulsarEntity):
    """Entity for Pulsar M water meters."""

    def __init__(self, unique_id: str, pulsar_device: PulsarM, **kwargs: Any) -> None:
        """Initialize Pulsar M entity."""
        super().__init__(unique_id, pulsar_device, **kwargs)
