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
* **How do I see the current flow rate then?** Switch on **Live mode (5 min)**. It polls every 30 seconds for 5 minutes and then returns to the normal interval by itself. Use it occasionally: the short burst is fine, permanent fast polling is not. For permanent real-time flow monitoring a dedicated local flow sensor is still the better choice.
* **And during a regeneration?** **Track regeneration live** (off by default) polls every minute while a regeneration runs, for at most 60 minutes.
* **Does reading settings and daily values count against the limit?** No. Device information, settings and daily values come from read-only cloud endpoints that do not wake the device. They are read hourly or with the **Fetch settings now** button.
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

The integration provides the sensor **Data last changed** (diagnostic). It shows when the telemetry last changed. If it does not change for hours although water is used, the data is frozen.

Further indicators:
1. **Device error**: If the physical device has an unacknowledged error, it stops uploading telemetry. If *Device error* is on, the other values are likely frozen.
2. **Flow vs. capacity**: If water is running but the remaining capacity does not decrease over several polls, the connection between the device and the cloud has frozen.

---

### 6. Which models are supported?
The integration is tested on a **softliQ SE21**. The model is detected from the series and type reported by the cloud (for the SE series the type is 100 + size, e.g. 121 = SE21). On the **SE18** the salt warning and LED ring entities are not created, because the SE18 has no salt level sensor and no LED ring. Devices of other series (e.g. **softliQ SD**) keep the exchanger 2 sensors. New controls appear only if the cloud reports the matching parameter. If you own another model, please open an issue with a diagnostics download.

---

### 7. Why is "Last regeneration" unknown?
The cloud reports neither the time of the last regeneration nor a regeneration history (the history shown on the device display is stored on the device only). The integration records a regeneration when the regeneration count increases, so the sensor is unknown until the first regeneration after installation. With **Track regeneration live** the time is accurate to about one minute, otherwise to the polling interval.

---

### 8. How do I find out which cloud parameter belongs to an option in the app?
Change the option in the Grünbeck app, wait about a minute and press **Fetch settings now**. The sensor **Changed settings** lists the changed parameter with old and new value in its `changes` attribute. The list is also part of the diagnostics download. This is how the iQ-Mode, signal and LED ring controls were mapped.

---

### 9. Is the integration available in other languages?
Entity names, states, attributes and device names are translated to English and German and follow the language of the user profile. The `description` attribute follows the system language of Home Assistant. Other languages fall back to English; translations are welcome.
