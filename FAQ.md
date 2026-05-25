# Frequently Asked Questions (FAQ)

Here are the answers to the most common questions regarding the **Grünbeck Cloud SE Series** Home Assistant integration.

---

### 1. What was the motivation for creating this integration?
This integration was specifically created due to the incompatibility of the general-purpose [hagruenbeck_cloud](https://github.com/p0l0/hagruenbeck_cloud) integration with the **SE / SD series** devices (such as `softliQ.SE` and `softliQ.SD`). 

The standard integration struggled with SE devices due to outdated API schemas. This custom component was built to provide a specific, robust solution for the SE/SD series that focuses on **stable, low-frequency monitoring of basic parameters** (such as capacities, salt range, error states, and long-term water consumption statistics) at a safe 10-to-60 minute interval. 

> [!IMPORTANT]
> If you own a different model (such as the `softliQ.SC` series, which supports direct offline local LAN polling) or prefer general-purpose cloud polling, you should continue using **[hagruenbeck_cloud](https://github.com/p0l0/hagruenbeck_cloud)** instead.

---

### 2. Why do my sensor updates sometimes freeze?
Anecdotally, users have noticed that telemetry updates can occasionally freeze, leaving sensor states unchanged (or showing as "unknown") both in Home Assistant and in the official Grünbeck mobile app.

There are two primary causes for these freezes:
* **Physical Device Errors**: If your water softener displays a physical error or warning on its physical display screen (e.g., salt low or maintenance required), it **stops uploading telemetry to the Grünbeck Cloud**. Acknowledge/clear the warning on the physical touch panel to immediately resume updates.
* **Cloud Rate Limiting (Excessive Polling)**: If the integration is configured to poll at an aggressive, high-frequency rate (like sub-minute intervals), Grünbeck's cloud gateway (Azure IoT Hub) will throttle the wake-up commands. The cloud API will continue responding with `200 OK` using old cached data, but the physical device will cease telemetry uploads, freezing your data for both this integration and the official app. Ensure your polling interval is set to at least **10 minutes** to avoid this.

---

### 3. What is the motivation behind the configurable polling interval and rate limiting?
We have made the polling interval fully configurable between **10 minutes** and **60 minutes** (with a default of **10 minutes**).

* **Why?** Since the SE series lacks a local API, all updates must be requested from Grünbeck’s cloud servers. Aggressive sub-minute polling (like 10–15 seconds) triggers severe cloud-side rate-limiting at the Azure API Gateway and IoT Hub levels. When throttled, the cloud silently stops dispatching wake-up commands to the physical device. As a result, your device ceases telemetry uploads, and both the official app and Home Assistant will display frozen data from hours ago.
* **Why are flow rates and regeneration status disabled by default?** Because these metrics change on a second-by-second basis and are not meaningful when checked at a 10-to-60 minute interval. You can still manually enable them in Home Assistant if needed, but a dedicated local smart flow sensor is far superior for real-time water monitoring.

---

### 4. Is this integration officially supported by Grünbeck? What is their attitude towards open APIs?
**No. This integration is entirely unofficial and is not supported, endorsed, or maintained by Grünbeck in any way.**

Grünbeck's overall openness to open APIs or local integrations for their newer cloud-connected devices (like the `softliQ:SD` and `softliQ:SE` series) is highly limited:
* Older series (like `softliQ:SC`) had a direct, unencrypted local web server/Mux interface that allowed local LAN polling.
* Newer series (`SD` and `SE` models) have removed these local access endpoints and are hardwired to route all traffic exclusively through their proprietary Azure-hosted cloud API.
* As discussed in the community threads (and [issue #117](https://github.com/p0l0/hagruenbeck_cloud/issues/117)), Grünbeck does not provide public API documentation or support third-party smart home integrations, meaning the community must rely on reverse-engineered cloud sequences to pull their own device telemetry into systems like Home Assistant.

---

### 5. How can I detect if the telemetry data has become stale or frozen?
Because the Grünbeck Cloud API will still respond with `200 OK` and a valid JSON payload containing your last cached state even if your physical device has been offline or frozen for days, there is no direct "offline" status field in the JSON payload itself. 

However, you can easily detect a frozen state using these indicators:
1. **Check the "Device Error" Sensor**: If the physical device has an unacknowledged error, it stops uploading telemetry entirely. If `binary_sensor.device_error` is in a `Problem` state, your other sensor metrics are likely frozen.
2. **Verify flow vs. capacity changes**: If water is running (e.g., your flow rate is above zero) but your remaining capacities do not decrease at all over several minutes, the connection between the device and the cloud has frozen.
3. **Lovelace / Template Alert**: You can build a Home Assistant template helper to alert you if the `last_changed` timestamp of your total `sensor.calculated_water_consumption` has not updated for a prolonged period (e.g., 6 hours), which indicates an inactive cloud feed.

