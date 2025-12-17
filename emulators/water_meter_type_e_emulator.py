"""Pulsar Water Meter Type E Emulator - Electronic Meters (Gen 1).

Returns Float32 volume and flow rate values with parameter-based diagnostics.
"""

from __future__ import annotations

from datetime import datetime

from base_emulator import BaseEmulator
from config_loader import load_config, get_device_config


class WaterMeterTypeEEmulator(BaseEmulator):
    """Type E: Electronic Gen 1 emulator (Float32 format, channel 2 flow rate)."""

    def __init__(self, port: int | None = None, config_path: str | None = None):
        """Initialize Type E water meter emulator.

        Args:
            port: TCP port to listen on. If None, uses config value.
            config_path: Path to config file. If None, uses default.
        """
        # Load configuration
        config = load_config(config_path)
        device_config = get_device_config(config, "water_meter_type_e")

        # Extract configuration values
        self.device_id = device_config["device_id"]
        self.device_address = device_config["address"]
        self.port = port if port is not None else device_config["port"]

        # Channel data (Float32)
        channels = device_config["channels"]
        self.channel_1_volume_forward = channels["volume_forward"]
        self.channel_2_flow_rate = channels["flow_rate"]

        # Parameters
        params = device_config["parameters"]
        self.battery_voltage = params["battery_voltage"]  # mV (UINT16)
        self.error_flags = params["error_flags"]  # UINT16
        self.rssi = params.get("rssi", -70)  # INT8, dBm

        # Firmware version
        fw = device_config["firmware"]
        self.fw_number = fw["fw_number"]
        self.hw_version = fw["hw_version"]
        self.sw_version = fw["sw_version"]
        self.revision = fw["revision"]
        self.modification = fw["modification"]

        super().__init__(
            device_address=self.device_address,
            device_id=self.device_id,
            port=self.port,
        )

    def get_channel_data(self, channel_mask: int) -> bytes | None:
        """Get channel data for Type E water meter.

        Type E has Channel 1 (Volume Forward) and Channel 2 (Flow Rate) as Float32.

        Args:
            channel_mask: Bitmask of channels to read.

        Returns:
            Channel data bytes or None if invalid.
        """
        if channel_mask == 0:
            return None

        channel_data = bytearray()

        # Channel 1: Volume Forward (Float32)
        if channel_mask & 0x01:
            channel_data.extend(self.encode_float32(self.channel_1_volume_forward))

        # Channel 2: Flow Rate (Float32)
        if channel_mask & 0x02:
            channel_data.extend(self.encode_float32(self.channel_2_flow_rate))

        # Reject if requesting other channels
        if channel_mask & ~0x03:  # Only bits 0 and 1 are valid (0x01, 0x02)
            return None

        return bytes(channel_data) if len(channel_data) > 0 else None

    def get_parameter(self, param_index: int) -> bytes | None:
        """Get parameter value for Type E water meter.

        Args:
            param_index: Parameter index.

        Returns:
            Parameter value (8 bytes) or None if not found.
        """
        result = bytearray(8)

        if param_index == 0x0000:
            # Device ID (UINT16)
            result[0:2] = self.encode_uint(self.device_id, 2)

        elif param_index == 0x0001:
            # Network Address (UINT32)
            result[0:4] = self.encode_uint(self.device_address, 4)

        elif param_index == 0x0002:
            # Firmware Version (UINT64)
            result[0:2] = self.encode_uint(self.fw_number, 2)
            result[2:4] = self.encode_uint(self.hw_version, 2)
            result[4:6] = self.encode_uint(self.sw_version, 2)
            result[6] = self.revision
            result[7] = self.modification

        elif param_index == 0x0040:
            # Battery Voltage (UINT16, mV)
            result[0:2] = self.encode_uint(self.battery_voltage, 2)

        elif param_index == 0x0010:
            # Error Flags (UINT16, bitmask)
            result[0:2] = self.encode_uint(self.error_flags, 2)

        elif param_index == 0x0206:
            # RSSI (INT8, dBm)
            rssi_byte = self.rssi & 0xFF
            if self.rssi < 0:
                rssi_byte = (self.rssi + 256) & 0xFF
            result[0] = rssi_byte

        else:
            return None

        return bytes(result)

    def get_archive_data(
        self,
        channel_mask: int,
        archive_type: int,
        date_start: datetime,
        date_end: datetime,
    ) -> bytes | None:
        """Get archive data for Type E water meter (Float32 format).

        Args:
            channel_mask: Single channel mask (must be 0x01 or 0x02).
            archive_type: Archive type (1=hourly, 2=daily, 3=monthly).
            date_start: Start datetime.
            date_end: End datetime.

        Returns:
            Archive data or None if invalid.
        """
        # Validate that only one channel is requested
        if channel_mask == 0 or (channel_mask & (channel_mask - 1)) != 0:
            return None

        if channel_mask not in [0x01, 0x02]:
            return None

        if archive_type not in [1, 2, 3]:
            return None

        # Determine base value
        base_value = (
            self.channel_1_volume_forward
            if channel_mask == 0x01
            else self.channel_2_flow_rate
        )

        response = bytearray()
        response.extend(self.encode_uint(channel_mask, 4))
        response.extend(self.encode_datetime(date_start))

        # Generate archive records (Float32 format)
        if archive_type == 1:
            num_records = min(
                24, int((date_end - date_start).total_seconds() / 3600) + 1
            )
            increment = 0.5 if channel_mask == 0x01 else 0.1
            for i in range(num_records):
                value = base_value + (i * increment)
                response.extend(self.encode_float32(value))

        elif archive_type == 2:
            num_records = min(7, (date_end - date_start).days + 1)
            increment = 12.0 if channel_mask == 0x01 else 2.0
            for i in range(num_records):
                value = base_value + (i * increment)
                response.extend(self.encode_float32(value))

        elif archive_type == 3:
            num_records = min(
                3,
                (
                    (date_end.year - date_start.year) * 12
                    + date_end.month
                    - date_start.month
                )
                + 1,
            )
            increment = 360.0 if channel_mask == 0x01 else 60.0
            for i in range(num_records):
                value = base_value + (i * increment)
                response.extend(self.encode_float32(value))

        return bytes(response)


def main():
    """Run the Type E water meter emulator."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Pulsar Water Meter Type E Emulator (Electronic Gen 1)"
    )
    parser.add_argument(
        "--port", type=int, default=9605, help="TCP port to listen on (default: 9605)"
    )
    args = parser.parse_args()

    emulator = WaterMeterTypeEEmulator(port=args.port)
    try:
        emulator.start()
    except KeyboardInterrupt:
        print("\nShutting down...")
        emulator.stop()


if __name__ == "__main__":
    main()
