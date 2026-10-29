# Grünbeck Cloud SE Series for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

A custom integration for cloud-connected **Grünbeck softliQ SE** water softeners (`softliQ.SE`: SE18, SE21, SE24). Devices of other series that use the same cloud API (e.g. `softliQ.SD`) keep working as before; see [Supported devices](#supported-devices).

The integration monitors the softener at a cloud-safe interval and adds what the cloud offers beyond the live telemetry: daily water and salt values, device information, settings, controls for the settings that are also available in the Grünbeck app, and maintenance tracking. All entity names, states and descriptions are available in **English and German** and follow the language of Home Assistant.

> [!WARNING]
> **Is a Grünbeck softener right for your smart home?**
> * **No local API**: The `softliQ.SD` and `softliQ.SE` series have no local API. All data goes through Grünbeck's cloud.
> * **Strict rate limits**: Polling the live telemetry more often than about once a minute for a longer time makes the cloud stop forwarding requests to the device. The data then freezes for 1–3 hours, in Home Assistant and in the Grünbeck app. The default interval is **10 minutes**.
>
> For the `softliQ.SC` series (local LAN access) or general-purpose cloud polling, see **[hagruenbeck_cloud](https://github.com/p0l0/hagruenbeck_cloud)**.

> [!IMPORTANT]
> **Library conflict**: Home Assistant can load only one version of `pygruenbeck_cloud`. Uninstall `hagruenbeck_cloud` and restart Home Assistant before installing this integration, otherwise login fails (`Unable to login`).

---

## Features

* **Live telemetry** (default every 10 minutes, configurable 10–60): remaining capacity, flow rate, regeneration phase, regeneration count, error and salt state.
* **Cloud data without waking the device** (hourly): device information and error list, settings, daily water, lime and salt values. These endpoints only read the cloud cache and do not count against the rate limit.
* **Controls** like in the Grünbeck app: iQ-Mode, signal on failure, LED ring options and brightness.
* **Live mode**: polls every 30 seconds for 5 minutes, e.g. to see the current flow rate, then returns to the normal interval by itself.
* **Regeneration tracking** (opt-in): polls every minute while a regeneration runs (max. 60 minutes).
* **Calculated water consumption** for the Energy dashboard, derived from the remaining capacity.
* **Regeneration history**: time of the last regeneration and the last 20 regenerations with the remaining capacity before each one. The cloud does not provide this, so it is recorded by Home Assistant.
* **Maintenance and inspection tracking**: next due date from the intervals configured in the device, editable date of the last service and "done" buttons.
* **Frozen data detection**: a timestamp of the last change in the telemetry.
* **Setting change log**: records which cloud parameter changed, e.g. after changing an option in the app.
* **Descriptions**: every entity has a `description` attribute explaining what it shows, in the language of Home Assistant.
* **Diagnostics download** with the raw cloud responses (credentials and serial numbers redacted).

---

## Supported devices

| Device | Status |
|---|---|
| softliQ SE21 (type 121) | Tested, all controls verified on a real device |
| softliQ SE18 (type 118) | Expected to work; no salt warning, LED ring or leakage entities (not present on the SE18) |
| softliQ SE24 (type 124) | Expected to work like the SE21 |
| softliQ SD and other series | Behaves as before: exchanger 2 sensors are kept. New controls appear only if the cloud reports the matching parameter. Not verified |

The model is detected from the series and type reported by the cloud and shown on the device page (e.g. "softliQ SE21"). Reports from other models are welcome: please attach a diagnostics download to an issue.

---

## Entities

Entities are grouped into the main device and four sub-devices, linked via "Connected via" on the device page.

### Main device

| Platform | Entity | Description |
|---|---|---|
| `sensor` | Remaining capacity | Soft water left until the next regeneration (`L`) |
| `sensor` | Remaining capacity percent | Remaining capacity in `%` |
| `sensor` | Flow rate | Current soft water flow (`L/min`). Only up to date in live mode or while water is running during a poll |
| `sensor` | Regeneration phase | Inactive, filling the brine tank, brining, displacement, backwashing, washing out (raw value as attribute) |
| `sensor` | Regeneration count | Number of regenerations since start-up |
| `sensor` | Last regeneration | Detected when the regeneration count increases. Attribute `history`: last 20 regenerations |
| `sensor` | Next regeneration window | Next configured regeneration time. In iQ-Mode the device decides itself whether it regenerates then |
| `sensor` | Last error | Message of the newest open error, `OK` if none. Attribute `errors`: full list |
| `sensor` | Chlorine cell current | Current of the disinfection cell (`mA`), only non-zero during disinfection |
| `sensor` | Software version, Start-up date | Device information (diagnostic) |
| `sensor` | Regeneration status | Raw status code (disabled by default) |
| `sensor` | Last poll | Time of the last successful poll of the telemetry (diagnostic) |
| `sensor` | Data last changed | Time of the last change in the telemetry (diagnostic) |
| `sensor` | Changed settings | Time of the last changed setting, attribute `changes` with the last changes (diagnostic) |
| `binary_sensor` | Device error | On if the device reports an error |
| `binary_sensor` | Salt warning | On if the salt supply is low (not on the SE18) |
| `binary_sensor` | Regeneration running | On while a regeneration step is active |
| `switch` | Live mode (5 min) | Poll every 30 s for 5 minutes |
| `button` | Fetch settings now | Read device information and settings immediately (does not wake the device) |

On devices with two exchangers (not the softliQ SE) the main device also has *Remaining capacity exchanger 2*, *Remaining capacity exchanger 2 percent*, *Flow exchanger 2* and *Blended flow*.

### Consumption

| Platform | Entity | Description |
|---|---|---|
| `sensor` | Calculated water consumption | Lifetime total in `L`, for the Energy dashboard |
| `sensor` | Average flow rate (last interval) | Average flow between the last two polls (`L/min`) |
| `sensor` | Water volume 0 °dH | Soft water meter of the device (`m³`, whole m³) |
| `sensor` | Make-up water | Water used to refill the brine tank (`L`) |
| `sensor` | Salt usage | Total salt usage reported by the device (`kg`). Stays at 0 on some SE devices, use *Salt usage sum of daily values* instead |

### Daily values

| Platform | Entity | Description |
|---|---|---|
| `sensor` | Water usage yesterday | `L`; attribute `daily` with the last 14 days |
| `sensor` | Lime retained yesterday | `g` |
| `sensor` | Salt usage yesterday | `g` |
| `sensor` | Salt usage sum of daily values | `kg`, sum of all daily values the cloud returns |

The cloud only provides completed days, so there is no value for today.

### Maintenance

| Platform | Entity | Description |
|---|---|---|
| `date` | Last maintenance, Last inspection | Stored in Home Assistant (the cloud does not know them). Default: start-up date |
| `button` | Maintenance done, Inspection done | Set the date to today |
| `sensor` | Next maintenance, Next inspection | Last date plus the interval configured in the device |
| `sensor` | Days until maintenance, Days until inspection | Negative when overdue |
| `sensor` | Maintenance interval | From the device (`d`) |

### Settings

| Platform | Entity | Description |
|---|---|---|
| `switch` | iQ-Mode | On: the device chooses the regeneration time itself. Off: regeneration at the fixed times only |
| `switch` | Signal on failure | Acoustic signal on failures, leakage and frost warnings |
| `switch` | LED ring permanently on / on failure / on message / on flow | As in the app. The device stores one value, so the switches depend on each other: *permanently on* switches the others off, *on message* includes *on failure*, *on flow* includes both |
| `number` | LED ring brightness | 0–100 % |
| `switch` | Track regeneration live | Opt-in, see [Polling](#polling-and-rate-limits) |
| `sensor` | Raw water hardness, Soft water hardness setpoint, Regeneration times, Nominal flow rate, Regeneration capacity | From the device settings |

Changed settings are first shown as pending by the cloud until the device has picked them up.

---

## Polling and rate limits

| Mode | Interval | Duration |
|---|---|---|
| Normal | 10 minutes (configurable 10–60) | permanent |
| Live mode | 30 seconds | 5 minutes, then back to normal |
| Track regeneration live | 1 minute | while a regeneration runs, max. 60 minutes |
| Device info, settings, daily values | 1 hour (or the *Fetch settings now* button) | permanent, does not wake the device |

Live mode and regeneration tracking poll faster than the normal interval for a limited time. Use them occasionally; if the data freezes afterwards, wait for the cloud to recover.

---

## Installation

### HACS (recommended)

1. In **HACS**, open the three-dot menu and select **Custom repositories**.
2. Add `https://github.com/sventiffe/gruenbeck_cloud_se` with category **Integration**.
3. Download the integration and restart Home Assistant.

### Manual

Copy `custom_components/gruenbeck_cloud_se/` into `config/custom_components/` and restart Home Assistant.

## Configuration

1. **Settings → Devices & services → Add integration**, search for **Grünbeck Cloud SE Series**.
2. Enter your Grünbeck cloud login. Use exactly the email address the account was registered with (e.g. `@googlemail.com` vs. `@gmail.com`).
3. Select your softener.

Via **Configure** on the integration card you can change the password and the polling interval at any time.

### Upgrading from 0.1.x

Entities that no longer exist (exchanger 2 on softliQ SE devices, sensors that are always 0, the operation mode and regeneration button) are removed automatically on startup. Entity IDs of existing entities do not change. The unit of *Make-up water* changed from `m³` to `L`; Home Assistant may report a unit change under **Developer tools → Statistics**, which can be confirmed there. *Regeneration status* no longer has a state class (it is a status code, not a measurement); Home Assistant then offers to delete its old long-term statistics, which is safe.

---

## Water consumption dashboards

*Calculated water consumption* has `device_class: water` and `state_class: total_increasing`:

* **Energy dashboard**: **Settings → Dashboards → Energy → Water consumption → Add water source**, select *Calculated water consumption*.
* **Daily/weekly counters**: create a **Utility meter** helper with *Calculated water consumption* as input sensor.

The sensor ignores the transient `0 L` capacity during regeneration, so capacity resets are not counted as usage.

---

## Known limitations

* The cloud provides no time of the last or next regeneration and no regeneration history. The integration records regenerations from the next one after installation.
* A manual regeneration cannot be started via the cloud on the SE series (`POST /regenerate` returns 404).
* The leakage protection is not exposed by the cloud. A leakage alarm arrives as a device error.
* Operation modes (Eco/Comfort/Power) do not exist on the SE series and are not offered.

## Troubleshooting

If the device shows an unacknowledged error on its display, it stops sending telemetry and the data freezes in the app and in Home Assistant. Acknowledge the error on the device. *Data last changed* shows since when the data has not changed.

For bug reports, attach the diagnostics download (**Settings → Devices & services → Grünbeck Cloud SE Series → ⋮ → Download diagnostics**). Credentials and serial numbers are redacted.

---

## Development

Tests run against recorded (anonymized) cloud responses of a softliQ SE21, without a Grünbeck account:

```bash
pip install -r requirements_test.txt
pytest
```

---

This integration is not affiliated with or supported by Grünbeck.
