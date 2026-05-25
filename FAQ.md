# Frequently Asked Questions (FAQ)

Here are the answers to the most common questions regarding the **Grünbeck Cloud SE Series** Home Assistant integration.

---

### 1. What was the motivation for creating this integration?
This integration was specifically created due to the incompatibility of the general-purpose [hagruenbeck_cloud](https://github.com/p0l0/hagruenbeck_cloud) integration with the **SE / SD series** devices (such as `softliQ.SE` and `softliQ.SD`). 

The standard integration struggled with SE devices due to outdated API schemas and infrequent polling loops. The issue is tracked in detail on GitHub under [hagruenbeck_cloud Issue #117](https://github.com/p0l0/hagruenbeck_cloud/issues/117). This custom component was built to provide a high-frequency, real-time 5-step cloud refresh sequence designed explicitly for the SE series.

---

### 2. Why do my sensor updates sometimes freeze?
Anecdotally, users have noticed that telemetry updates can occasionally freeze, leaving sensor states unchanged (or showing as "unknown") both in Home Assistant and in the official Grünbeck mobile app.

* **What triggers this?** It is currently unclear what exactly triggers these freezes, but they are often tied to the physical device. Specifically, if your water softener displays a physical error or warning on its physical display screen, it **stops uploading telemetry to the Grünbeck Cloud**.
* **How to fix it?** Simply walk over to your physical water softener and acknowledge/clear the error on the physical display. Once the error is cleared, the device will immediately resume sending telemetry, and Home Assistant will resume real-time updates automatically.

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
* As discussed in the community threads (and issue #117), Grünbeck does not provide public API documentation or support third-party smart home integrations, meaning the community must rely on reverse-engineered cloud sequences to pull their own device telemetry into systems like Home Assistant.

---

### 5. How can I detect if the telemetry data has become stale or frozen?
Because the Grünbeck Cloud API will still respond with `200 OK` and a valid JSON payload containing your last cached state even if your physical device has been offline or frozen for days, there is no direct "offline" status field in the JSON payload itself. 

However, you can easily detect a frozen state using these indicators:
1. **Check the "Device Error" Sensor**: If the physical device has an unacknowledged error, it stops uploading telemetry entirely. If `binary_sensor.device_error` is in a `Problem` state, your other sensor metrics are likely frozen.
2. **Verify flow vs. capacity changes**: If water is running (e.g., your flow rate is above zero) but your remaining capacities do not decrease at all over several minutes, the connection between the device and the cloud has frozen.
3. **Lovelace / Template Alert**: You can build a Home Assistant template helper to alert you if the `last_changed` timestamp of your total `sensor.calculated_water_consumption` has not updated for a prolonged period (e.g., 6 hours), which indicates an inactive cloud feed.

