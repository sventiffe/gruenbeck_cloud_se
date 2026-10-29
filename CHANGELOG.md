# Changelog

## 0.2.0

### Added
* Device information, settings and daily water/lime/salt values from read-only cloud endpoints (hourly, does not wake the device).
* Sensors: regeneration phase (text), last regeneration with history, next regeneration window, last error, software version, start-up date, chlorine cell current, soft water meter, make-up water, average flow rate, daily values, last poll, data last changed, changed settings.
* Binary sensor: regeneration running.
* Controls: iQ-Mode, signal on failure, LED ring options (4 switches as in the app), LED ring brightness.
* Live mode (30 s for 5 minutes) and opt-in regeneration tracking (1 min while a regeneration runs).
* Maintenance and inspection tracking: last date (editable, stored locally), "done" buttons, next date and days remaining.
* Button "Fetch settings now".
* English and German translations for all entities, states, attributes, device names and errors.
* `description` attribute with an explanation for every entity.
* Entities grouped into sub-devices (consumption, daily values, maintenance, settings).
* Model detection (e.g. "softliQ SE21"); entities depend on the model.
* Diagnostics download with raw cloud responses (redacted).
* Automated tests (`pytest`) with recorded cloud responses, replacing `simulate.py`.

### Changed
* Sub-devices are linked with `via_device_id`; `via_device` in `DeviceInfo` makes entity setup fail on Home Assistant 2026.10.
* Flow rate unit is `L/min` (verified on a softliQ SE21; was `m³/h`), flow rate sensor enabled by default.
* Make-up water unit is `L` (was `m³`), matching the Grünbeck app.
* Regeneration status has no state class anymore, so the history no longer shows averaged status codes.

### Removed
* Exchanger 2 and blended flow sensors on softliQ SE devices (single exchanger; the values never changed). Kept on other series.
* Salt warning on the softliQ SE18 (no salt level sensor).
* Obsolete entities are removed from the entity registry automatically on startup.
