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
We have made the polling interval fully configurable down to a minimum of **10 seconds** (with a default of **15 seconds**). However, we strongly suggest keeping the interval moderate.

* **Why?** Since the SE series lacks a local API, all updates must be requested from Grünbeck’s cloud servers. High-frequency polling (like 10–15s) increases the load on Grünbeck’s end. 
* To ensure the stability of the integration and to keep the load on Grünbeck's cloud moderate—preventing them from implementing harsh rate limits or IP blocking—consider setting the polling interval to a slightly higher value (e.g. 30–60 seconds) if real-time sub-minute flow rates are not actively required for your automation needs.

---

### 4. Is this integration officially supported by Grünbeck? What is their attitude towards open APIs?
**No. This integration is entirely unofficial and is not supported, endorsed, or maintained by Grünbeck in any way.**

Grünbeck's overall openness to open APIs or local integrations for their newer cloud-connected devices (like the `softliQ:SD` and `softliQ:SE` series) is highly limited:
* Older series (like `softliQ:SC`) had a direct, unencrypted local web server/Mux interface that allowed local LAN polling.
* Newer series (`SD` and `SE` models) have removed these local access endpoints and are hardwired to route all traffic exclusively through their proprietary Azure-hosted cloud API.
* As discussed in the community threads (and issue #117), Grünbeck does not provide public API documentation or support third-party smart home integrations, meaning the community must rely on reverse-engineered cloud sequences to pull their own device telemetry into systems like Home Assistant.
