"""Tests for setup, entities and controls."""
from __future__ import annotations

import pytest
from homeassistant.helpers import device_registry as dr, entity_registry as er

from .conftest import DEVICE_ID, DOMAIN


async def test_setup_creates_entities(hass, setup_integration):
    """All main entities are created with English names."""
    await setup_integration()

    assert hass.states.get("sensor.grunbeck_softliq_se_remaining_capacity").state == "300.0"
    assert hass.states.get("sensor.grunbeck_softliq_se_regeneration_phase").state == "inactive"
    assert hass.states.get("sensor.grunbeck_softliq_se_last_error").state == "OK"
    assert hass.states.get("sensor.grunbeck_consumption_make_up_water").attributes[
        "unit_of_measurement"
    ] == "L"
    assert hass.states.get("switch.grunbeck_settings_iq_mode").state == "on"
    assert hass.states.get("switch.grunbeck_settings_signal_on_failure").state == "on"
    # Each entity explains itself
    assert hass.states.get("sensor.grunbeck_softliq_se_flow_rate").attributes["description"]


async def test_german_names(hass, setup_integration):
    """Names follow the language of Home Assistant."""
    await setup_integration("de")
    state = hass.states.get("sensor.grunbeck_softliq_se_restkapazitat")
    assert state.attributes["friendly_name"] == "Grünbeck SoftliQ SE Restkapazität"
    assert state.attributes["description"].startswith("Weichwassermenge")


async def test_sub_devices_linked(hass, setup_integration):
    """The group devices are linked to the main device."""
    entry = await setup_integration()
    registry = dr.async_get(hass)
    devices = dr.async_entries_for_config_entry(registry, entry.entry_id)
    main = next(d for d in devices if (DOMAIN, DEVICE_ID) in d.identifiers)
    assert main.model == "softliQ SE21"
    groups = [d for d in devices if d is not main]
    assert len(groups) == 4
    assert all(d.via_device_id == main.id for d in groups)


async def test_obsolete_entities_removed(hass, setup_integration):
    """Exchanger 2 and other entities of 0.1.x are removed on the softliQ SE."""
    registry = er.async_get(hass)
    old = {}

    def create_old(entry):
        for domain, key in (("sensor", "mRescapa2"), ("button", "regenerate")):
            old[key] = registry.async_get_or_create(
                domain, DOMAIN, f"{DEVICE_ID}_{key}", config_entry=entry
            ).entity_id

    await setup_integration(before=create_old)
    assert all(registry.async_get(entity_id) is None for entity_id in old.values())


async def test_unreported_fields_removed(hass, setup_integration):
    """Sensors of /update fields the device does not report are not kept."""
    registry = er.async_get(hass)
    old = {}

    def create_old(entry):
        old["mcurrent"] = registry.async_get_or_create(
            "sensor", DOMAIN, f"{DEVICE_ID}_mcurrent", config_entry=entry
        ).entity_id

    await setup_integration(before=create_old)
    assert registry.async_get(old["mcurrent"]) is None


@pytest.mark.parametrize(
    ("series", "device_type", "model", "salt", "led", "exchanger_2"),
    [
        ("softliQ.SE", 118, "softliQ SE18", False, False, False),
        ("softliQ.SE", 124, "softliQ SE24", True, True, False),
        ("softliQ.D", 115, "softliQ.D", True, True, True),
    ],
)
async def test_model_features(
    hass, setup_integration, cloud_data, series, device_type, model, salt, led, exchanger_2
):
    """Entities depend on the model."""
    for part in ("update", "info"):
        cloud_data[part].update({"series": series, "type": device_type})
    entry = await setup_integration()
    keys = {
        e.unique_id.removeprefix(f"{DEVICE_ID}_")
        for e in er.async_entries_for_config_entry(er.async_get(hass), entry.entry_id)
    }
    assert ("salt_warning" in keys) is salt
    assert ("led_ring_failure" in keys) is led
    assert ("mRescapa2" in keys) is exchanger_2
    main = dr.async_get(hass).async_get_device(identifiers={(DOMAIN, DEVICE_ID)})
    assert main.model == model


async def test_iq_mode_switch(hass, setup_integration, cloud):
    """iQ-Mode off means fixed regeneration times (pregmode true)."""
    await setup_integration()
    await hass.services.async_call(
        "switch", "turn_off", {"entity_id": "switch.grunbeck_settings_iq_mode"}, blocking=True
    )
    assert cloud.calls[-1] == ("PATCH", "/parameters", {"pregmode": True})
    assert hass.states.get("switch.grunbeck_settings_iq_mode").state == "off"


@pytest.mark.parametrize(
    ("start", "action", "switch", "expected"),
    [
        (8, "turn_on", "permanently_on", 1),
        (1, "turn_on", "on_message", 4),
        (2, "turn_on", "on_flow", 8),
        (8, "turn_off", "on_message", 2),
        (8, "turn_off", "on_failure", 0),
        (0, "turn_on", "on_failure", 2),
    ],
)
async def test_led_ring_switches(
    hass, setup_integration, cloud, cloud_data, start, action, switch, expected
):
    """The LED ring switches are coupled like in the app."""
    cloud_data["parameters"]["pled"] = start
    await setup_integration()
    await hass.services.async_call(
        "switch", action, {"entity_id": f"switch.grunbeck_settings_led_ring_{switch}"}, blocking=True
    )
    assert cloud.calls[-1] == ("PATCH", "/parameters", {"pled": expected})


async def test_setting_changes_are_logged(hass, setup_integration, cloud_data):
    """A setting changed in the app shows up in the change log."""
    await setup_integration()
    cloud_data["parameters"]["pled"] = 2
    await hass.services.async_call(
        "button", "press", {"entity_id": "button.grunbeck_softliq_se_fetch_settings_now"}, blocking=True
    )
    await hass.async_block_till_done()
    state = hass.states.get("sensor.grunbeck_softliq_se_changed_settings")
    assert state.attributes["changes"][0].endswith("pled: 8 → 2")
    assert hass.states.get("switch.grunbeck_settings_led_ring_on_message").state == "off"


async def test_unload(hass, setup_integration):
    """The config entry unloads cleanly."""
    entry = await setup_integration()
    assert await hass.config_entries.async_unload(entry.entry_id)
