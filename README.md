# Grünbeck Cloud SE Series for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![Community Forum](https://img.shields.io/badge/community-forum-brightgreen.svg)](https://community.home-assistant.io/)

A custom, low-frequency monitoring integration specifically designed for **Grünbeck SE Series** (`softliQ.SE`, `softliQ.SD`) cloud-connected water softeners.

> [!WARNING]
> **Is a Grünbeck Softener right for your Smart Home?**
> If you are currently shopping for a water softener and plan to integrate it deeply into your smart home (e.g. Home Assistant), **Grünbeck might not be your best choice.**
> * **No Local API**: Newer models (`softliQ.SD` and `softliQ.SE` series) do not offer a local API. All data must route through Grünbeck's proprietary, closed Azure-hosted cloud servers.
> * **Strict Rate Limits**: High-frequency sub-minute polling (like 15 seconds) will trigger severe cloud-side rate limiting (C2D MQTT command throttling), completely freezing your telemetry and making both this integration and your official mobile app show stale data.
> * **Our Approach**: This integration is designed specifically for **low-frequency monitoring** of slow-moving basic parameters (capacities, salt levels, error states, and long-term water consumption statistics) at a safe **10 to 60-minute interval** (defaulting to 10 minutes) to keep your cloud connection perfectly stable.
>
> If you own a different Grünbeck model (such as the `softliQ.SC` series, which supports local offline LAN polling) or prefer general-purpose cloud polling, you should consider using **[hagruenbeck_cloud](https://github.com/p0l0/hagruenbeck_cloud)** instead.

> [!IMPORTANT]
> **Prerequisites & Library Conflicts**
> Home Assistant restricts loading multiple versions of the same dependency library (`pygruenbeck_cloud`). If you currently have the general-purpose `hagruenbeck_cloud` integration installed, you **must completely uninstall it and restart Home Assistant** before installing this integration to avoid library dependency conflicts (`Unable to login`).

---

## Key Features

*   **Low-Frequency Monitoring (Configurable 10–60m, Default 10m)**: Polls exchanger capacities, percentages, salt levels, and error states dynamically at a cloud-safe interval.
*   **Duplex Calculated Water Consumption**: Water consumption is not directly reported by the cloud API. This integration solves that by monitoring capacity decreases across **both** Exchangers (duplex system) and accumulating precise water consumption in Liters (`L`), persisting it safely across Home Assistant restarts.
*   **Registry-Disabled Fast Sensors**: Rapidly changing parameters (like flow rates and regeneration status) are disabled by default in the Home Assistant registry. Because they change on a second-by-second basis physically, catching them on a 10-minute cloud polling cycle will mostly result in stale or zero values, so they are kept disabled by default to avoid cluttering your dashboard. You can manually re-enable them in the entity settings if desired.
*   **User-Friendly Config Flow**: Set up the integration directly via the Home Assistant integrations frontend (simply input your username and password, then select your water softener from the discovered list).

---

## Entities Provided

| Platform | Entity Name | Description | Default Registry State |
|---|---|---|---|
| `sensor` | Exchanger 1 Remaining Capacity | Remaining soft water capacity for Exchanger 1 in Liters (`L`) | **Enabled** |
| `sensor` | Exchanger 2 Remaining Capacity | Remaining soft water capacity for Exchanger 2 in Liters (`L`) | **Enabled** |
| `sensor` | Exchanger 1 Remaining Capacity Percent | Percentage remaining for Exchanger 1 Exchanger (`%`) | **Enabled** |
| `sensor` | Exchanger 2 Remaining Capacity Percent | Percentage remaining for Exchanger 2 Exchanger (`%`) | **Enabled** |
| `sensor` | Exchanger 1 Flow Rate | Live soft water flow rate through Exchanger 1 (`m³/h`) | *Disabled by default* |
| `sensor` | Exchanger 2 Flow Rate | Live soft water flow rate through Exchanger 2 (`m³/h`) | *Disabled by default* |
| `sensor` | Blended Flow Rate | Combined soft water flow rate (`m³/h`) | *Disabled by default* |
| `sensor` | Calculated Water Consumption | High-precision total accumulated water consumption (`L`), ideal for utility meters | **Enabled** |
| `sensor` | Salt Usage | Accumulated salt usage in kilograms (`kg`) | **Enabled** |
| `sensor` | Regeneration Capacity | Nominal soft water capacity (`m³`) | **Enabled** |
| `sensor` | Regeneration Count | Number of regenerations performed | **Enabled** |
| `sensor` | Regeneration Status | Current operational phase of regeneration | *Disabled by default* |
| `binary_sensor` | Device Error | Active problem state if the softener reports any internal errors | **Enabled** |
| `binary_sensor` | Salt Warning | Active problem state if salt levels are low or need attention | **Enabled** |

---

## Installation

### Method 1: HACS (Recommended)

1.  Open **Home Assistant**, go to **HACS** -> **Integrations**.
2.  Click the three dots in the top-right corner and select **Custom repositories**.
3.  Enter the URL of your GitHub repository: `https://github.com/sventiffe/gruenbeck_cloud_se` and select **Integration** as the category.
4.  Click **Add**.
5.  Click on the newly added integration and click **Download**.
6.  Restart Home Assistant.

### Method 2: Manual Installation

1.  Download the repository content as a ZIP file.
2.  Copy the folder `custom_components/gruenbeck_cloud_se/` from the ZIP into your Home Assistant's `config/custom_components/` directory.
3.  Restart Home Assistant.

---

## Configuration

1.  In the Home Assistant UI, navigate to **Settings** -> **Devices & Services**.
2.  Click **Add Integration** in the bottom-right corner.
3.  Search for **Grünbeck Cloud SE Series** and select it.
4.  Enter your Grünbeck Cloud username and password.
5.  Select your discovered water softener device from the dropdown and complete setup.

### Dynamic Options (Password & Polling Interval)

Once configured, you can click the **Configure** (German: *Konfigurieren*) button on the integration's card in **Settings -> Devices & Services** to dynamically manage your settings without having to delete the integration or lose your calculated water consumption total:
* **Cloud Password**: Easily update your password if you rotate it. The integration will securely re-authenticate with the Grünbeck Cloud automatically.
* **Polling Interval**: Adjust the cloud polling frequency in minutes. The default is **10 minutes**, with a configurable range of **10 to 60 minutes** to remain completely safe from cloud-side rate-limiting and telemetry freezes (see [FAQ.md](file:///Users/sven/homeassistant/FAQ.md) for rate-limiting guidelines).

---

## Calculated Water Consumption & Dashboards

The **Calculated Water Consumption** sensor is a continuous, lifetime accumulator (acting like a physical utility/smart water meter). It starts at `0.0 L` on installation and increases indefinitely, safely persisting across Home Assistant restarts.

To prevent false water consumption spikes, the sensor automatically filters out any remaining capacity updates of exactly `0.0 L`. During active regeneration cycles, the device temporarily drops the offline exchanger's remaining capacity to `0.0 L` before resetting it to full capacity. By ignoring this transient `0.0 L` state, the integration ensures that capacity resets or purges are never falsely recorded as water usage.

Since it is configured with `device_class: water` and `state_class: total_increasing`, it integrates natively with Home Assistant. Below are two popular methods to set up dashboards for tracking your daily, weekly, or monthly water usage.

### Method A: Home Assistant Native "Energy & Water" Dashboard (Recommended)

Home Assistant has a built-in dashboard dedicated to utility metrics. It automatically handles all hourly, daily, weekly, and monthly calculations and builds beautiful bar charts:

1. Go to **Settings** -> **Dashboards** -> **Energy** (German: *Einstellungen* -> *Dashboards* -> *Energie*).
2. Scroll down to the **Water Consumption** (*Wasserverbrauch*) section.
3. Click **Add Water Source** (*Wasserquelle hinzufügen*).
4. Select **Calculated Water Consumption** from the dropdown.
5. Click **Save**.

*Within 1-2 hours, Home Assistant will begin displaying beautiful, native bar graphs tracking your usage over time.*

### Method B: Lovelace Dashboard Cards (Daily/Weekly Resets)

If you want to display exact numeric values on your main Lovelace dashboard that reset on a fixed cycle (e.g. at midnight or at the end of the week):

1. Go to **Settings** -> **Devices & Services** -> **Helpers** (*Einstellungen* -> *Geräte & Dienste* -> *Helfer*).
2. Click **Create Helper** (*Helfer erstellen*) in the bottom-right corner.
3. Select **Utility Meter** (*Verbrauchszähler*).
4. Configure a **Daily** counter:
   * **Name**: `Daily Water Consumption`
   * **Input Sensor**: `Calculated Water Consumption` (`sensor.calculated_water_consumption`)
   * **Meter reset cycle**: `Daily`
5. Click **Create**.
6. Repeat the same steps to create a **Weekly** helper (selecting `Weekly` as the reset cycle).

This creates two new sensors (`sensor.daily_water_consumption` and `sensor.weekly_water_consumption`) which you can add to standard Lovelace cards (like Gauge, History Graph, or Stat cards) on your main dashboard!

---

## Local Verification & Testing

This project includes a fully mocked local simulator script to validate code and fetch real-time metrics completely independent of a live Home Assistant environment:

```bash
# Execute simulator using your virtual environment
./gruenbeck-venv/bin/python simulate.py
```

---

## Troubleshooting & Device Telemetry

> [!TIP]
> **Active Device Error & Frozen Telemetry**
> If your physical Grünbeck water softener has an active, unacknowledged error shown on its display:
> 1. The device will **stop sending new telemetry data** to the Grünbeck Cloud.
> 2. The official Grünbeck mobile app will show frozen/outdated data.
> 3. This Home Assistant integration's **Device Error** binary sensor will switch to `Problem`, and all other sensor values will stop updating (appearing frozen).
> 
> **How to resolve**: Simply walk over to your physical water softener and acknowledge/clear the active error on its display screen. Telemetry transmission to the cloud will immediately resume, the **Device Error** binary sensor will return to `OK`, and the integration will instantly resume receiving live data.

