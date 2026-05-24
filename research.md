# Grünbeck SE Series Cloud API Research

This document captures our findings on the Grünbeck Cloud API for the SE series based on the proof of concept script `gruenbeck.neu.py` and direct cloud API tests.

## Cloud API Realtime Polling Protocol

Grünbeck devices do not push updates continuously, and the standard API doesn't poll frequently. The proof of concept script achieves real-time data by triggering a **5-step sequence** using the Grünbeck Cloud OAuth token:

1. **POST** `https://prod-eu-gruenbeck-api.azurewebsites.net/api/devices/{DEVICE_ID}/realtime/refresh?api-version=2024-05-02`
2. **POST** `https://prod-eu-gruenbeck-api.azurewebsites.net/api/devices/{DEVICE_ID}/realtime/enter?api-version=2024-05-02`
3. **GET**  `https://prod-eu-gruenbeck-api.azurewebsites.net/api/devices/{DEVICE_ID}/update?api-version=2024-05-02` (Retrieves the JSON dataset)
4. **POST** `https://prod-eu-gruenbeck-api.azurewebsites.net/api/devices/{DEVICE_ID}/realtime/leave?api-version=2024-05-02`
5. **POST** `https://prod-eu-gruenbeck-api.azurewebsites.net/api/devices/{DEVICE_ID}/realtime/off?api-version=2024-05-02`

By executing this sequence on a 60-second polling interval (via a Home Assistant `DataUpdateCoordinator`), we can fetch fresh data on every update cycle. It is important to stick to this sequence and not to optimize it by removing any of the steps, otherwise you will not get fresh data from the device.

---

## Response Data Structure & Mapping

The GET `/update` endpoint returns a JSON payload. Below is a sample response retrieved from a live `softliQ.SE` device (YOUR_DEVICE_NAME, `softliQ.SE/YOUR_SERIAL_NUMBER`):

```json
{
  "hasError": true,
  "id": "softliQ.SE/YOUR_SERIAL_NUMBER",
  "iregtrig": "0",
  "isRegistered": false,
  "mRescapa2": 933.0,
  "mcapacity": 6.0,
  "mcountreg": 218,
  "mcountwater1": 46,
  "mcountwatertank": 85,
  "mflow1": 0.0,
  "mflow2": 0.0,
  "mflowblend": 0.0,
  "mflowreg2": 0.0,
  "mlime": 13,
  "mregpercent2": 0,
  "mregstatus": 0,
  "mrescapa1": 331.0,
  "mresidcap1": 82,
  "mresidcap2": 233,
  "mreswatadmod": 0.0,
  "msaltrange": true,
  "msaltusage": 36.0,
  "mstep2": false,
  "mtemp": -9.0,
  "name": "YOUR_DEVICE_NAME",
  "register": false,
  "serialNumber": "YOUR_SERIAL_NUMBER",
  "series": "softliQ.SE",
  "type": 118
}
```

### Proposed Sensors Mapping

Based on the payload, we can define the following sensors in Home Assistant:

| Cloud Field | Sensor Name | Type / Class | Unit | Description |
|---|---|---|---|---|
| `mrescapa1` | Soft Water Capacity Left 1 | Sensor (`volume`) | `L` | Soft water remaining capacity for exchanger 1 |
| `mRescapa2` | Soft Water Capacity Left 2 | Sensor (`volume`) | `L` | Soft water remaining capacity for exchanger 2 |
| `mresidcap1` | Exchanger Remaining Capacity 1 | Sensor (`battery` / `%`) | `%` | Percentage capacity remaining for exchanger 1 |
| `mresidcap2` | Exchanger Remaining Capacity 2 | Sensor (`battery` / `%`) | `%` | Percentage capacity remaining for exchanger 2 |
| `mcapacity` | Regeneration Capacity | Sensor (`volume`) | `m³` | Nominal soft water capacity |
| `mcountreg` | Regeneration Count | Sensor (`numeric`) | — | Number of regenerations |
| `msaltusage` | Salt Usage | Sensor (`weight`) | `kg` | Amount of salt used |
| `mflow1` | Water Flow Rate 1 | Sensor (`water` flow) | `m³/h` | Flow rate through exchanger 1 |
| `mflow2` | Water Flow Rate 2 | Sensor (`water` flow) | `m³/h` | Flow rate through exchanger 2 |
| `mflowblend` | Blended Water Flow Rate | Sensor (`water` flow) | `m³/h` | Combined water flow rate |
| `mregstatus` | Regeneration Status | Sensor (`numeric`) | — | Current state of regeneration |
| `msaltrange` | Salt Range Warning | Binary Sensor (`problem`) | — | Status of salt level/range |
| `hasError` | Device Error State | Binary Sensor (`problem`) | — | True if device reports an error |

---

## Total Water Consumption Calculation Strategy

As noted in the user request:
1. There is no direct "total water consumption" field in the cloud API.
2. The remaining capacity fields (`mrescapa1`, `mRescapa2`) count down to `0` until a regeneration happens, at which point they reset to a higher capacity (e.g. 331L or more).
3. We can track the total soft water consumed by:
   - Calculating the difference between successive polls: $\Delta = \text{previous\_value} - \text{current\_value}$.
   - If $\Delta > 0$, add $\Delta$ to the accumulated total consumption sensor.
   - If $\Delta \le 0$ (e.g. device regenerated or no change), ignore the difference.
4. To persist this accumulated value across Home Assistant restarts, we will make the Sensor Entity inherit from `RestoreEntity`. On setup, we fetch the last state via `await self.async_get_last_state()` and continue accumulating.

---

## Technical Architecture for the Scaffolding

We will structure the new integration in `/Users/sven/homeassistant/custom_components/gruenbeck_cloud_se/` with:
- `manifest.json`: Metadata, dependencies, codeowners.
- `const.py`: Shared constants.
- `__init__.py`: Component initialization & config entry setup.
- `config_flow.py`: High-quality setup GUI that:
  - Validates credentials with the Grünbeck Cloud API.
  - Fetches the user's list of devices.
  - Lets them select their device.
- `coordinator.py`: Core polling mechanism that runs the 5-step sequence on a 60-second timer.
- `sensor.py` and `binary_sensor.py`: Platform-specific entity setups.
- `entity.py`: Base entity class containing standard device information.

---

## Device Telemetry & Physical Error Behavior

Real-world testing has confirmed a critical behavior regarding device error handling and the Grünbeck Cloud API:

1. **Telemetry Freeze**: When the physical Grünbeck water softener experiences and displays an active error message on its device screen, **it ceases all telemetry uploads** to the cloud.
2. **State Impact**:
   - The cloud API continues responding, but all metrics (flow rates, capacities, etc.) represent frozen/outdated states.
   - The mobile app and this integration will display stale, frozen numbers.
   - The `hasError` payload field will remain `true`, exposing a `Problem` state in Home Assistant's `Device Error` binary sensor.
3. **Recovery Flow**: Once the error is physically acknowledged/cleared on the device's display screen, the softener immediately resumes telemetry transmissions. The `Device Error` sensor in Home Assistant returns to `OK` (or `false`), and live sensor updates resume instantly.

---

## Intentionally Excluded Parameters

The following parameters returned by the `/update` JSON payload are intentionally **not** exposed as sensors in Home Assistant to maintain a clean entity registry and avoid redundant or low-resolution metrics:

*   **`mcountwater1` & `mcountwatertank`**: These represent lifetime water meters in cubic meters (`m³`). However, because they only update in integer increments of $1\text{ m³}$ ($1,000\text{ Liters}$), they lack the granularity needed for modern smart home tracking. The integration's custom calculated total water consumption sensor offers far superior liter-level high-resolution tracking.
*   **`mlime`**: Represents the raw input water hardness (e.g. `14` °dH). Because this is a static configuration value set on the device that does not change over time, it is not useful as a time-series sensor.
*   **`mtemp`**: Represents a temperature probe value (e.g. `-9.0`). In the SE/SD series, this sensor is unused or returns static error values, providing no functional utility.
*   **`mflowreg2` / `mregpercent2` / `mstep2`**: Technical details about Exchanger 2 regeneration steps. These are highly specific operational details that do not add value to day-to-day smart home monitoring.


