"""Model specific features of the supported Grünbeck devices.

The cloud reports a series (e.g. "softliQ.SE") and a numeric type. For the
softliQ SE the type is 100 + model size (118 = SE18, 121 = SE21,
124 = SE24). Features that are only known to be missing are switched off,
everything else behaves as before for unknown devices.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

SERIES_SE = "softliQ.SE"
# softliQ SE18: no salt level sensor, no LED ring, no leakage sensor
SE_TYPES_WITHOUT_SALT_SENSOR = {118}
SE_TYPES_WITHOUT_LED_RING = {118}


@dataclass(frozen=True)
class DeviceFeatures:
    """Features of the connected device."""

    series: str | None
    device_type: int | None
    model: str
    # The SE series has a single exchanger. Other series (e.g. softliQ.SD)
    # may have two, so the exchanger 2 entities are kept there.
    second_exchanger: bool
    salt_sensor: bool
    led_ring: bool


def device_features(data: dict[str, Any] | None) -> DeviceFeatures:
    """Return the features for the cloud data of a device."""
    data = data or {}
    info = data.get("_info") or {}
    series = data.get("series") or info.get("series")
    try:
        device_type = int(data.get("type") or info.get("type"))
    except (TypeError, ValueError):
        device_type = None

    is_se = series == SERIES_SE
    if is_se and device_type is not None and 100 < device_type < 200:
        model = f"softliQ SE{device_type - 100}"
    else:
        model = series or "softliQ"

    return DeviceFeatures(
        series=series,
        device_type=device_type,
        model=model,
        second_exchanger=not is_se,
        salt_sensor=not (is_se and device_type in SE_TYPES_WITHOUT_SALT_SENSOR),
        led_ring=not (is_se and device_type in SE_TYPES_WITHOUT_LED_RING),
    )
