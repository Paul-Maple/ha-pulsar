"""DataUpdateCoordinator for Pulsar devices."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DATA_KEY_BATTERY_VOLTAGE,
    DATA_KEY_CURRENT_WATER_CONSUMPTION_CH1,
    DATA_KEY_DEVICE_TEMPERATURE,
    DATA_KEY_SYSTEM_TIME,
    DEFAULT_SCAN_INTERVAL,
)
from .pulsardevice import PulsarDevice

_LOGGER = logging.getLogger(__name__)


class PulsarDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator to fetch data from Pulsar device."""

    def __init__(
        self, hass: HomeAssistant, device: PulsarDevice, device_id: str
    ) -> None:
        """Initialize coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"Pulsar {device.name}",
            update_interval=DEFAULT_SCAN_INTERVAL,
        )
        self.device = device
        self.device_id = device_id

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from device (in executor to avoid blocking)."""
        try:
            return await self.hass.async_add_executor_job(self._fetch_data)
        except Exception as err:
            raise UpdateFailed(f"Error communicating with device: {err}") from err

    def _fetch_data(self) -> dict[str, Any]:
        """Fetch all metrics for device (runs in thread pool)."""
        data: dict[str, Any] = {}
        # Get all sensor keys for this device type
        sensor_keys = [
            DATA_KEY_CURRENT_WATER_CONSUMPTION_CH1,
            DATA_KEY_SYSTEM_TIME,
            DATA_KEY_DEVICE_TEMPERATURE,
            DATA_KEY_BATTERY_VOLTAGE,
        ]

        # Fetch all metrics in one batch
        # Note: Individual key failures are logged but don't stop the update
        for key in sensor_keys:
            try:
                value = self.device.getdata(key)
                if value is not None:
                    data[key] = value
            except (ConnectionError, TimeoutError, OSError) as err:
                _LOGGER.warning(
                    "Failed to fetch %s for device %s: %s", key, self.device.name, err
                )
            except Exception as err:  # pylint: disable=broad-except
                # Catch other exceptions (protocol errors, parsing errors, etc.)
                # but log them as warnings to not break the entire update
                _LOGGER.warning(
                    "Error fetching %s for device %s: %s", key, self.device.name, err
                )

        return data
