"""Constants for the Grünbeck Cloud SE Series integration."""

import logging

DOMAIN = "gruenbeck_cloud_se"

CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_DEVICE_ID = "device_id"
CONF_SCAN_INTERVAL = "scan_interval"

# Polling interval in minutes (default 10 minutes)
DEFAULT_SCAN_INTERVAL = 10

# Interval in minutes for the plain cloud endpoints (device info, parameters,
# daily measurements). These are read from the cloud cache and do not send
# commands to the device, but they change rarely.
EXTRA_SCAN_INTERVAL = 60

# Live mode: poll the realtime sequence more often for a short time only,
# to stay clear of the cloud-side rate limiting.
LIVE_MODE_DURATION = 300  # seconds
LIVE_MODE_INTERVAL = 30  # seconds

# Optional faster polling while a regeneration is running
REGENERATION_TRACKING_INTERVAL = 60  # seconds
REGENERATION_TRACKING_MAX = 60  # minutes

API_BASE_URL = "https://prod-eu-gruenbeck-api.azurewebsites.net/api/devices"
API_VERSION = "2024-05-02"

# Mappings taken from pygruenbeck_cloud
REGENERATION_STEPS = {
    0: "inactive",
    10: "fill_salt_tank",
    20: "salting",
    30: "displacement",
    40: "backwashing",
    50: "backwashing",
    60: "washing_out",
}

LOGGER = logging.getLogger(__package__)


# LED ring (pled), confirmed on a softliQ SE21. The app shows four switches,
# but the device stores one value: each level includes the ones before it
# (failure -> message -> flow), "permanent" excludes the others.
LED_RING_OFF = 0
LED_RING_PERMANENT = 1
# Switch key -> value; in ascending order
LED_RING_LEVELS = {
    "led_ring_failure": 2,
    "led_ring_message": 4,
    "led_ring_flow": 8,
}
