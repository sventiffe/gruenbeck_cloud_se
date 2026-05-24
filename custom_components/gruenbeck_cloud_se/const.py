"""Constants for the Grünbeck Cloud SE Series integration."""

import logging

DOMAIN = "gruenbeck_cloud_se"

CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_DEVICE_ID = "device_id"

# Polling interval (1 minute)
DEFAULT_SCAN_INTERVAL = 60

LOGGER = logging.getLogger(__package__)
