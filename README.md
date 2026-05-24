# Grünbeck Cloud SE Series for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![Community Forum](https://img.shields.io/badge/community-forum-brightgreen.svg)](https://community.home-assistant.io/)

A custom, high-frequency real-time Home Assistant integration specifically designed for **Grünbeck SE Series** (`softliQ.SE`, `softliQ.SD`) cloud-connected water softeners. 

Unlike general-purpose cloud integrations that poll infrequently, this integration implements a dedicated **5-step real-time connection sequence** that forces a cloud refresh and polls live device metrics every **60 seconds**, capturing precise flow rates and water status.

> [!IMPORTANT]
> **Prerequisites & Incompatibility Warnings**
> 1. **Uninstall Legacy Integrations First**: Home Assistant restricts loading multiple versions of the same dependency library (`pygruenbeck_cloud`). If you currently have the general-purpose `hagruenbeck_cloud` integration installed, you **must completely uninstall it and restart Home Assistant** before installing this integration to avoid library dependency conflicts (`Unable to login`).
> 2. **Email Domain Login Sensitivity**: The Grünbeck Cloud API login is strictly domain-sensitive. You must enter your exact registered email address (e.g. `@googlemail.com` vs `@gmail.com` as appropriate).

---


## Key Features

*   **Real-time Polling (60s Updates)**: Polls exchanger capacities, percentages, flow rates, salt levels, and error states dynamically.
*   **Duplex Calculated Water Consumption**: Water consumption is not directly reported by the Grünbeck API. This integration solves that by monitoring capacity decreases across **both** Exchangers (duplex system) and accumulating precise water consumption in Liters (`L`), persisting it safely across Home Assistant restarts.
*   **User-Friendly Config Flow**: Set up the integration directly via the Home Assistant integrations frontend (simply input your username and password, then select your water softener from the discovered list).
*   **HACS Ready**: Formatted according to the standard HACS custom repository layout.

---

## Entities Provided

| Platform | Entity Name | Description |
|---|---|---|
| `sensor` | Exchanger 1 Remaining Capacity | Remaining soft water capacity for Exchanger 1 in Liters (`L`) |
| `sensor` | Exchanger 2 Remaining Capacity | Remaining soft water capacity for Exchanger 2 in Liters (`L`) |
| `sensor` | Exchanger 1 Remaining Capacity Percent | Percentage remaining for Exchanger 1 Exchanger (`%`) |
| `sensor` | Exchanger 2 Remaining Capacity Percent | Percentage remaining for Exchanger 2 Exchanger (`%`) |
| `sensor` | Exchanger 1 Flow Rate | Live soft water flow rate through Exchanger 1 (`m³/h`) |
| `sensor` | Exchanger 2 Flow Rate | Live soft water flow rate through Exchanger 2 (`m³/h`) |
| `sensor` | Blended Flow Rate | Combined soft water flow rate (`m³/h`) |
| `sensor` | Calculated Water Consumption | High-precision total accumulated water consumption (`L`), ideal for utility meters |
| `sensor` | Salt Usage | Accumulated salt usage in kilograms (`kg`) |
| `sensor` | Regeneration Capacity | Nominal soft water capacity (`m³`) |
| `sensor` | Regeneration Count | Number of regenerations performed |
| `sensor` | Regeneration Status | Current operational phase of regeneration |
| `binary_sensor` | Device Error | Active problem state if the softener reports any internal errors |
| `binary_sensor` | Salt Warning | Active problem state if salt levels are low or need attention |

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
5.  Select your discovered water softener device (e.g. *YOUR_DEVICE_NAME*) from the dropdown and complete setup.

---

## Local Verification & Testing

This project includes a fully mocked local simulator script to validate code and fetch real-time metrics completely independent of a live Home Assistant environment:

```bash
# Execute simulator using your virtual environment
./gruenbeck-venv/bin/python simulate.py
```
