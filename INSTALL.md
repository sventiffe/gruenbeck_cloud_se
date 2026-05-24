# Installation and Setup Guide

This guide explains how to install and configure the **Grünbeck Cloud SE Series** custom Home Assistant integration.

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
6. Select your discovered device (e.g. *YOUR_DEVICE_NAME*) from the dropdown and complete the setup!
