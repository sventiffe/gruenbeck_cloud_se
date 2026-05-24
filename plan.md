# Project Plan: Grünbeck Cloud SE Integration

This integration provides a fresh, dedicated solution for Grünbeck SE Series water softeners, solving the limitation where real-time values are not updated properly in general-purpose cloud integrations.

## Phase 1: Foundation & Scaffolding
- [x] Initialize git repository and set up standard repository files (`.gitignore`, `README.md`).
- [x] Implement `manifest.json` with `pygruenbeck_cloud==1.3.3` dependency.
- [x] Create `const.py` for shared domain configuration, logging, and key definitions.
- [x] Create `config_flow.py` to prompt for Grünbeck cloud credentials, connect to the cloud, fetch available devices, and let the user select their specific device.
- [x] Implement `__init__.py` to manage integration setup and teardown.

## Phase 2: Data Update Coordinator
- [x] Create `coordinator.py` featuring the 5-step realtime cloud refresh sequence.
- [x] Configure it to poll data every 60 seconds.
- [x] Add exception handling and auto-reauthentication/refresh if the OAuth access token expires.

## Phase 3: Sensor Entities
- [x] Design base entity class (`entity.py`) to link all entities to the softliQ device.
- [x] Implement `sensor.py` exposing:
  - Exchanger 1 and Exchanger 2 remaining capacities.
  - Exchanger remaining capacity percentages.
  - Nomad regeneration capacity.
  - Water flow rates, combined flow rate.
  - Regeneration counts, salt usages.
- [x] Implement `binary_sensor.py` exposing:
  - Device error states.
  - Salt range warning status.

## Phase 4: Persisted Water Consumption Sensor
- [x] Implement a calculated sensor for accumulated water consumption using `RestoreEntity`.
- [x] Track successive negative differences in capacity remaining to measure water consumed.
- [x] Ignore positive differences caused by device regenerations.
- [x] Validate recovery of accumulated values across simulated entity restarts.

## Phase 5: Verification & Distribution Prep
- [x] Validate component structure against Home Assistant core requirements.
- [x] Test loading in a mock environment or verify config flow using a test script.
- [x] Prepare standard HACS info file (`hacs.json`).
- [x] Prepare the integration for github publication.
