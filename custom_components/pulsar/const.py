"""Constants for the Pulsar integration."""

from datetime import timedelta

from homeassistant.const import Platform

DOMAIN = "pulsar"
MANUFACTURER = "Pulsar"

ADDR_SIZE = 4
FUNC_SIZE = 1
LEN_SIZE = 1
ID_SIZE = 2
CRC_SIZE = 2
SERVICE_SIZE = ADDR_SIZE + FUNC_SIZE + LEN_SIZE + ID_SIZE + CRC_SIZE
MAX_REQUEST_ID = 0xFFFF

CONF_ACTION = "action"
CONF_ENTITIES = "entities"
CONF_CONNECTOR = "connector"
CONF_DEVICE_CONFIG = "device_config"
CONF_DEVICE = "device"
CONF_DEVICE_OR_ADDRESS = "device_or_address"
CONF_ID = "id"
CONF_MANUAL_PATH = "Enter Manually"
CONF_NAME = "name"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_SERIAL_ID = "serial_id"
CONF_TYPE = "type"

STEP_ADD_MENU = "add_menu"
STEP_EDIT_DEVICE = "edit_device"
STEP_CHANGE_PORT = "change_port"
STEP_COMPLETE = "complete"
STEP_CONFIGURE_DEVICE = "configure_device"
STEP_CONFIGURE_MENU = "configure_menu"
STEP_CHOOSE_SERIAL_PORT = "choose_serial_port"
STEP_MANUAL_PORT_CONFIG = "manual_port_config"
STEP_SCAN_INTERVAL = "scan_interval"

DEFAULT_SCAN_INTERVAL = timedelta(seconds=60)

PLATFORMS = [
    Platform.SENSOR,
]
