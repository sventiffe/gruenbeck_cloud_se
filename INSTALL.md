# Installation and Setup Guide

This guide explains how to install and configure the **Grünbeck Cloud SE Series** custom Home Assistant integration.

> [!IMPORTANT]
> **Prerequisites & Incompatibilities**
> 1. **Uninstall Legacy Integrations First**: Home Assistant can only load one version of the underlying `pygruenbeck_cloud` library. If you have any other Grünbeck HACS integrations installed (such as the general-purpose `hagruenbeck_cloud` integration), you **must uninstall them completely and restart Home Assistant** before setting up this integration. Failure to do so will cause library version conflicts and result in `Unable to login` / connection failures.
> 2. **Email Domain Sensitivity**: The Grünbeck Cloud API is strictly domain-sensitive. You **must** use the exact email domain your account was registered with (e.g., `@googlemail.com` vs `@gmail.com`).

---


## Step 1: Add the Custom Repository to HACS

1. Open your **Home Assistant** frontend.
2. Click on **HACS** in the sidebar.
3. Click the **three dots** in the top-right corner and select **Custom repositories**.
4. In the **Repository** field, paste your GitHub repository URL:
   ```text
   https://github.com/sventiffe/gruenbeck_cloud_se
   ```
5. In the **Category** dropdown, select **Integration**.
6. Click **Add** and close the dialog.

---

## Step 2: Download the Integration

1. You should now see the **Grünbeck Cloud SE Series** integration card in the HACS dashboard (or search for it under Integrations).
2. Click on the integration card.
3. Click the **Download** button in the bottom-right corner.
4. Keep the default version selected and click **Download** to confirm.

---

## Step 3: Restart Home Assistant

1. In the Home Assistant sidebar, go to **Settings** -> **System**.
2. Click the **Restart** button in the top-right corner.
3. Select **Restart Home Assistant** to reload your custom components.

---

## Step 4: Add the Integration in Devices & Services

1. Once Home Assistant has restarted, go to **Settings** -> **Devices & Services**.
2. Click the **Add Integration** button in the bottom-right corner.
3. Search for **Grünbeck Cloud SE Series** and select it.
4. Enter your Grünbeck Cloud credentials:
   * **Username**: Your Grünbeck Cloud login email
   * **Password**: Your Grünbeck Cloud login password
5. The integration will automatically contact the cloud API, discover your water softeners, and display them.
6. Select your discovered device from the dropdown and complete setup!
*By default, the integration will poll every **10 minutes** to maintain API connection stability. You can adjust this interval between 10 and 60 minutes at any time by clicking the **Configure** button on the integration's card under Settings -> Devices & Services.*

---

## Post-Setup: Tracking Water Consumption

Once the integration is configured, it will expose the **Calculated Water Consumption** sensor. Because it behaves like a standard utility meter and has `total_increasing` metrics, you can configure beautiful water usage dashboards.

### Method A: Built-in Energy/Water Dashboard (Recommended)
1. Go to **Settings** -> **Dashboards** -> **Energy** (German: *Einstellungen* -> *Dashboards* -> *Energie*).
2. Scroll to the **Water Consumption** (*Wasserverbrauch*) section.
3. Click **Add Water Source** (*Wasserquelle hinzufügen*).
4. Select **Calculated Water Consumption** from the list and save.
*Home Assistant will start compiling and presenting gorgeous hourly/daily bar graphs of your water usage.*

### Method B: Lovelace Resets (Daily/Weekly Resets)
If you want exact numeric values on your main dashboard that reset at midnight or the weekend:
1. Go to **Settings** -> **Devices & Services** -> **Helpers** (*Einstellungen* -> *Geräte & Dienste* -> *Helfer*).
2. Click **Create Helper** -> Select **Utility Meter** (*Verbrauchszähler*).
3. Name it `Daily Water Consumption`, choose `Calculated Water Consumption` as input, and set the cycle to `Daily`. Click **Create**.
4. Repeat to create a `Weekly Water Consumption` sensor with a `Weekly` cycle.
*You can now display these new daily/weekly resetting sensors on any dashboard card (Gauge, Stat, or History Graph)!*

