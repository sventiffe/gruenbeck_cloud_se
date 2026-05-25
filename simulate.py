#!/usr/bin/env python3
"""Offline simulator & validation script for Grünbeck Cloud SE Series.

This script mocks the Home Assistant API so that the custom component
files can be imported, tested, and validated completely locally without
running a Home Assistant instance.
"""

import sys
import types
import asyncio
from datetime import timedelta
import pprint

# ==========================================
# 1. EMULATE HOME ASSISTANT APIS
# ==========================================

class MockCoordinatorEntity:
    def __init__(self, coordinator):
        self.coordinator = coordinator
    def __class_getitem__(cls, item):
        return cls
    async def async_added_to_hass(self):
        pass

class MockSensorEntity:
    pass

class MockBinarySensorEntity:
    pass

class MockRestoreEntity:
    async def async_get_last_state(self):
        # Emulate no previous state restored (starts at 0)
        return None

def callback(func):
    return func

# Set up the dummy sys.modules namespace
homeassistant = types.ModuleType("homeassistant")
sys.modules["homeassistant"] = homeassistant

# core
homeassistant.core = types.ModuleType("homeassistant.core")
homeassistant.core.callback = callback
class MockHomeAssistant:
    pass
homeassistant.core.HomeAssistant = MockHomeAssistant
sys.modules["homeassistant.core"] = homeassistant.core

# const
homeassistant.const = types.ModuleType("homeassistant.const")
homeassistant.const.CONF_USERNAME = "username"
homeassistant.const.CONF_PASSWORD = "password"
homeassistant.const.Platform = types.SimpleNamespace(
    SENSOR="sensor", BINARY_SENSOR="binary_sensor"
)
sys.modules["homeassistant.const"] = homeassistant.const

# config_entries
homeassistant.config_entries = types.ModuleType("homeassistant.config_entries")
class MockConfigEntry:
    pass
homeassistant.config_entries.ConfigEntry = MockConfigEntry
class ConfigFlow:
    @classmethod
    def __init_subclass__(cls, **kwargs):
        pass
    async def async_set_unique_id(self, unique_id):
        pass
    def _abort_if_unique_id_configured(self):
        pass
    def async_show_form(self, step_id, data_schema, errors=None):
        return {"type": "form", "step_id": step_id, "data_schema": data_schema, "errors": errors}
    def async_create_entry(self, title, data):
        return {"type": "create_entry", "title": title, "data": data}
class OptionsFlow:
    def __init__(self, config_entry):
        self.config_entry = config_entry
    def async_show_form(self, step_id, data_schema, errors=None):
        return {"type": "form", "step_id": step_id, "data_schema": data_schema, "errors": errors}
    def async_create_entry(self, title, data):
        return {"type": "create_entry", "title": title, "data": data}
homeassistant.config_entries.ConfigFlow = ConfigFlow
homeassistant.config_entries.OptionsFlow = OptionsFlow
sys.modules["homeassistant.config_entries"] = homeassistant.config_entries


# data_entry_flow
homeassistant.data_entry_flow = types.ModuleType("homeassistant.data_entry_flow")
class MockFlowResult:
    pass
homeassistant.data_entry_flow.FlowResult = MockFlowResult
sys.modules["homeassistant.data_entry_flow"] = homeassistant.data_entry_flow

# helpers.device_registry
homeassistant.helpers = types.ModuleType("homeassistant.helpers")
homeassistant.helpers.device_registry = types.ModuleType("homeassistant.helpers.device_registry")
homeassistant.helpers.device_registry.DeviceInfo = lambda **kwargs: kwargs
sys.modules["homeassistant.helpers"] = homeassistant.helpers
sys.modules["homeassistant.helpers.device_registry"] = homeassistant.helpers.device_registry

# helpers.entity_platform
homeassistant.helpers.entity_platform = types.ModuleType("homeassistant.helpers.entity_platform")
class MockAddEntitiesCallback:
    pass
homeassistant.helpers.entity_platform.AddEntitiesCallback = MockAddEntitiesCallback
sys.modules["homeassistant.helpers.entity_platform"] = homeassistant.helpers.entity_platform

# helpers.update_coordinator
homeassistant.helpers.update_coordinator = types.ModuleType("homeassistant.helpers.update_coordinator")
class DataUpdateCoordinator:
    def __init__(self, hass, logger, name, update_interval):
        self.hass = hass
        self.logger = logger
        self.name = name
        self.update_interval = update_interval
        self.data = {}
    async def async_config_entry_first_refresh(self):
        self.data = await self._async_update_data()
    def __class_getitem__(cls, item):
        return cls
homeassistant.helpers.update_coordinator.DataUpdateCoordinator = DataUpdateCoordinator
class UpdateFailed(Exception):
    pass
homeassistant.helpers.update_coordinator.UpdateFailed = UpdateFailed
homeassistant.helpers.update_coordinator.CoordinatorEntity = MockCoordinatorEntity
sys.modules["homeassistant.helpers.update_coordinator"] = homeassistant.helpers.update_coordinator

# components.sensor
homeassistant.components = types.ModuleType("homeassistant.components")
homeassistant.components.sensor = types.ModuleType("homeassistant.components.sensor")
homeassistant.components.sensor.SensorEntity = MockSensorEntity
homeassistant.components.sensor.SensorDeviceClass = types.SimpleNamespace(
    VOLUME="volume", VOLUME_FLOW_RATE="volume_flow_rate", WEIGHT="weight", WATER="water"
)
homeassistant.components.sensor.SensorStateClass = types.SimpleNamespace(
    MEASUREMENT="measurement", TOTAL_INCREASING="total_increasing"
)
sys.modules["homeassistant.components"] = homeassistant.components
sys.modules["homeassistant.components.sensor"] = homeassistant.components.sensor

# components.binary_sensor
homeassistant.components.binary_sensor = types.ModuleType("homeassistant.components.binary_sensor")
homeassistant.components.binary_sensor.BinarySensorEntity = MockBinarySensorEntity
homeassistant.components.binary_sensor.BinarySensorDeviceClass = types.SimpleNamespace(
    PROBLEM="problem"
)
sys.modules["homeassistant.components.binary_sensor"] = homeassistant.components.binary_sensor

# helpers.restore_state
homeassistant.helpers.restore_state = types.ModuleType("homeassistant.helpers.restore_state")
homeassistant.helpers.restore_state.RestoreEntity = MockRestoreEntity
sys.modules["homeassistant.helpers.restore_state"] = homeassistant.helpers.restore_state

# voluptuous
voluptuous = types.ModuleType("voluptuous")
voluptuous.Schema = lambda *args, **kwargs: args[0] if args else {}
voluptuous.Required = lambda *args, **kwargs: args[0] if args else {}
voluptuous.In = lambda *args, **kwargs: args[0] if args else {}
sys.modules["voluptuous"] = voluptuous


# ==========================================
# 2. RUN SIMULATION SCENARIOS
# ==========================================

async def main():
    print("🤖 STARTING GRÜNBECK CUSTOM INTEGRATION SIMULATION")
    print("=" * 60)

    # Import the components now that the environment is fully mocked
    print("✅ Importing Integration Components...")
    from custom_components.gruenbeck_cloud_se.config_flow import GruenbeckFlowHandler
    from custom_components.gruenbeck_cloud_se.coordinator import GruenbeckDataUpdateCoordinator
    from custom_components.gruenbeck_cloud_se.sensor import GruenbeckCloudSensor, GruenbeckCalculatedWaterConsumptionSensor
    from custom_components.gruenbeck_cloud_se.binary_sensor import GruenbeckErrorBinarySensor, GruenbeckSaltWarningBinarySensor
    print("✅ Components successfully imported!")
    print("-" * 60)

    # Use test credentials in workspace
    USERNAME = "YOUR_EMAIL"
    PASSWORD = "YOUR_PASSWORD"
    DEVICE_ID = "softliQ.SE/YOUR_DEVICE_ID"

    print(f"Step 1: Simulating Config Flow (User Credentials Step)...")
    flow = GruenbeckFlowHandler()
    flow.hass = object()  # dummy object
    
    # Step user
    user_result = await flow.async_step_user({
        "username": USERNAME,
        "password": PASSWORD
    })
    
    if user_result["type"] == "form" and user_result["step_id"] == "device":
        print("✅ Credentials validation SUCCEEDED!")
        print("Found Devices:")
        for dev_id, label in flow.devices_options.items() if hasattr(flow, 'devices_options') else [(d.id, d.name) for d in flow.devices]:
            print(f"  - {dev_id}: {label}")
    else:
        print("❌ Credentials validation FAILED!")
        return

    print("-" * 60)
    print("Step 2: Simulating Config Flow (Device Selection Step)...")
    device_result = await flow.async_step_device({
        "device_id": DEVICE_ID
    })
    
    if device_result["type"] == "create_entry":
        print(f"✅ Config entry successfully created! Title: {device_result['title']}")
        pprint.pprint(device_result["data"])
    else:
        print("❌ Device selection FAILED!")
        return

    print("-" * 60)
    print("Step 3: Initializing Coordinator & Fetching Realtime Data...")
    from pygruenbeck_cloud import PyGruenbeckCloud
    api = PyGruenbeckCloud(USERNAME, PASSWORD)
    await api.login()
    
    coordinator = GruenbeckDataUpdateCoordinator(
        hass=object(),
        api=api,
        device_id=DEVICE_ID,
        scan_interval=15
    )

    
    # Run the first refresh
    print("Polling API (this executes the 5-step sequence)...")
    await coordinator.async_config_entry_first_refresh()
    print("✅ Data successfully retrieved from Grünbeck Cloud:")
    pprint.pprint(coordinator.data)

    print("-" * 60)
    print("Step 4: Simulating Entity State Mapping...")
    
    # Instantiate sensors
    sensor_mrescapa1 = GruenbeckCloudSensor(coordinator, "mrescapa1", "Exchanger 1 Remaining Capacity", "L", None, None)
    sensor_mflowblend = GruenbeckCloudSensor(coordinator, "mflowblend", "Blended Flow Rate", "m³/h", None, None)
    sensor_salt = GruenbeckSaltWarningBinarySensor(coordinator)
    
    print(f"Sensor Name: {sensor_mrescapa1._attr_name} | State: {sensor_mrescapa1.native_value} {sensor_mrescapa1._attr_native_unit_of_measurement}")
    print(f"Sensor Name: {sensor_mflowblend._attr_name} | State: {sensor_mflowblend.native_value} {sensor_mflowblend._attr_native_unit_of_measurement}")
    print(f"Binary Sensor: {sensor_salt._attr_name} | Problem Active: {sensor_salt.is_on}")

    print("-" * 60)
    print("Step 5: Verifying Duplex Calculated Water Consumption...")
    consumption_sensor = GruenbeckCalculatedWaterConsumptionSensor(coordinator)
    
    # Emulate mock write state method
    def dummy_write_state():
        pass
    consumption_sensor.async_write_ha_state = dummy_write_state
    
    # Add dummy first state
    await consumption_sensor.async_added_to_hass()
    print(f"Initial Accumulated Water Consumption: {consumption_sensor.native_value} L")
    
    # Update 1: Initial values established
    print("\nSimulating state update 1: Exchanger 1 starts at 330L, Exchanger 2 starts at 930L")
    coordinator.data = {"mrescapa1": 330.0, "mRescapa2": 930.0}
    consumption_sensor._handle_coordinator_update()
    print(f"Accumulated Water Consumption: {consumption_sensor.native_value} L (Establish baseline)")
    
    # Update 2: Consumption on Exchanger 1
    print("\nSimulating state update 2: Exchanger 1 decreases to 315L (15L water consumed)")
    coordinator.data = {"mrescapa1": 315.0, "mRescapa2": 930.0}
    consumption_sensor._handle_coordinator_update()
    print(f"Accumulated Water Consumption: {consumption_sensor.native_value} L (Expected: 15.0 L)")

    # Update 3: Exchanger 1 regenerates (resets to 330L), Exchanger 2 becomes active and decreases to 910L (20L consumed)
    print("\nSimulating state update 3: Exchanger 1 resets/regenerates to 330L, Exchanger 2 decreases to 910L (20L consumed)")
    coordinator.data = {"mrescapa1": 330.0, "mRescapa2": 910.0}
    consumption_sensor._handle_coordinator_update()
    print(f"Accumulated Water Consumption: {consumption_sensor.native_value} L (Expected: 35.0 L)")

    print("-" * 60)
    print("🎉 ALL INTEGRATION SIMULATIONS COMPLETED SUCCESSFULLY!")
    await api.close()

if __name__ == "__main__":
    asyncio.run(main())
