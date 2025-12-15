[![](https://img.shields.io/github/release/KnyazSh/ha-pulsar/all.svg?style=for-the-badge)](https://github.com/KnyazSh/ha-pulsar/releases)
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)
[![](https://img.shields.io/github/license/KnyazSh/ha-pulsar?style=for-the-badge)](LICENSE)
[![](https://img.shields.io/badge/MAINTAINER-%40KnyazSh-red?style=for-the-badge)](https://github.com/KnyazSh)
[![](https://img.shields.io/badge/COMMUNITY-FORUM-success?style=for-the-badge)](https://community.home-assistant.io)

[![en](https://img.shields.io/badge/lang-en-red.svg?style=for-the-badge)](https://github.com/KnyazSh/ha-pulsar/blob/master/README.md)
[![ru](https://img.shields.io/badge/lang-ru-blue.svg?style=for-the-badge)](https://github.com/KnyazSh/ha-pulsar/blob/master/README.ru.md)

# Pulsar devices integration for Home Assistant

A Home Assistant custom integration to monitor [Pulsar smart metering devices](https://pulsarm.com/en/o-kompanii/) via RS-485 interface.

## Supported Devices

- **Pulsar-M Water Meters** with RS-485 interface
  - Example: [Water meter DU15 with RS-485](https://pulsarm.ru/products/schetchik-vody/kvartirnyy-schetchik-vody-du15-rs-485-pod-moduli-qn-1-5-m3-ch-l-110mm/)

## Requirements

- Home Assistant **2023.1** or newer
- RS-485 to USB adapter (or RS-485 to Ethernet converter)
- Python 3.10 or newer

## Installation

### Installation via HACS (Recommended)

1. Ensure [HACS](https://hacs.xyz/) is installed and working
2. Go to **HACS** > **Integrations**
3. Click the three dots in the top right corner
4. Select **Custom repositories**
5. Add this repository:
   - Repository: `KnyazSh/ha-pulsar`
   - Category: **Integration**
6. Click **Add**
7. Search for "Pulsar" in HACS
8. Click **Install**
9. Restart Home Assistant

### Manual Installation

1. Download the latest release from the [releases page](https://github.com/KnyazSh/ha-pulsar/releases)
2. Extract the archive
3. Copy the `custom_components/pulsar` folder to your Home Assistant `custom_components` directory:
   - For Home Assistant OS: `/config/custom_components/`
   - For Home Assistant Container: `/config/custom_components/`
   - For Home Assistant Core: `~/.homeassistant/custom_components/`
4. Restart Home Assistant

## Configuration

1. Go to **Settings** > **Devices & Services**
2. Click **Add Integration**
3. Search for **Pulsar**
4. Follow the setup wizard:
   - **Step 1**: Choose serial port
     - Select your RS-485 adapter from the list, or
     - Choose "Enter Manually" to specify a custom path (e.g., `/dev/ttyUSB0` or `192.168.1.100:1024` for TCP/IP)
   - **Step 2**: Configure device
     - Enter a friendly name for the device
     - Enter the device serial ID (address)
     - Select device type (currently only "pulsar-m-water" is available)
   - **Step 3**: Add more devices (optional)
     - Click "Add Device" to configure additional meters on the same RS-485 bus
     - Click "Complete" when finished

## Configuration Options

### Serial Port Configuration

- **Direct Serial**: Use device path like `/dev/ttyUSB0` (Linux) or `COM3` (Windows)
- **TCP/IP**: Use format `IP_ADDRESS:PORT` (e.g., `192.168.1.100:1024`) for serial-to-Ethernet converters

### Device Settings

- **Name**: Friendly name for the device (e.g., "Kitchen Water Meter")
- **Serial ID**: Device address on the RS-485 bus (numeric, typically 1-255)
- **Type**: Device type (currently only "pulsar-m-water" supported)

## Sensors

The integration creates the following sensors for each configured device:

- **Current Water Consumption**: Total water consumption in liters (increasing)
- **System Time**: Device internal clock time
- **Device Temperature**: Temperature of the meter in Celsius

## Troubleshooting

### Integration won't load

- **Check serial port**: Ensure the RS-485 adapter is connected and the port path is correct
- **Check permissions**: On Linux, ensure the user running Home Assistant has access to the serial port:
  ```bash
  sudo usermod -a -G dialout $USER
  ```
- **Check logs**: Review Home Assistant logs for error messages

### No data from sensors

- **Verify device address**: Ensure the serial ID matches the device configuration
- **Check RS-485 wiring**: Verify A/B lines are connected correctly
- **Check device power**: Ensure the meter is powered and operational
- **Review logs**: Check for communication errors in the logs

### Connection timeout errors

- **Increase timeout**: The default timeout is 3 seconds. If your device is slow, you may need to modify the connector timeout
- **Check bus load**: Too many devices on the RS-485 bus can cause communication issues
- **Verify baud rate**: Ensure all devices use the same baud rate (default: 9600)

## Removing the Integration

1. Go to **Settings** > **Devices & Services**
2. Find the **Pulsar** integration
3. Click on it
4. Click the three dots menu
5. Select **Delete**

## Adding Support for New Device Types

The integration is designed to be extensible. To add support for a new Pulsar device type:

1. Create a new device class in `custom_components/pulsar/pulsar_<device>.py` inheriting from `PulsarDevice`
2. Implement device-specific command methods
3. Override the `getdata(key: str)` method to return values for sensor keys
4. Add the device type to the `PulsarType` enum in `const.py`
5. Add sensor descriptions to the `SENSORS` dictionary in `sensor.py`
6. Update the factory logic in `pulsar_manager.py` to instantiate the new class

See the existing `pulsar_m_water.py` implementation as a reference.

## Development

### Code Quality

This integration follows Home Assistant development guidelines:

- Uses `DataUpdateCoordinator` for non-blocking updates
- All blocking I/O operations run in executor threads
- Type hints throughout the codebase
- Comprehensive error handling with custom exceptions

### Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Ensure code follows PEP 8 and Home Assistant style guidelines
5. Submit a pull request

## Support

- **Issues**: [GitHub Issues](https://github.com/KnyazSh/ha-pulsar/issues)
- **Community**: [Home Assistant Community Forum](https://community.home-assistant.io)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Credits

This component is developed by [KnyazSh](https://github.com/KnyazSh)

---

**Note**: This is a custom integration and is not part of the official Home Assistant distribution.
