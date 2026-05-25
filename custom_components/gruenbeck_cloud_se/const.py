"""Constants for the Grünbeck Cloud SE Series integration."""

import logging

DOMAIN = "gruenbeck_cloud_se"

CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_DEVICE_ID = "device_id"
CONF_SCAN_INTERVAL = "scan_interval"

# Polling interval in minutes (default 10 minutes)
DEFAULT_SCAN_INTERVAL = 10

LOGGER = logging.getLogger(__package__)

