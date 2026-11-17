[![hacs_badge](https://img.shields.io/badge/HACS-Default-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/v/release/Eugen417/GTC_VENTMACHINE_HA?style=for-the-badge)](https://github.com/Eugen417/GTC_VENTMACHINE_HA/releases)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-compatible-blue.svg?style=for-the-badge&logo=home-assistant)](https://www.home-assistant.io/)
[![GitHub Stars](https://img.shields.io/github/stars/Eugen417/GTC_VENTMACHINE_HA.svg?style=for-the-badge)](https://github.com/Eugen417/GTC_VENTMACHINE_HA/stargazers)
[![License](https://img.shields.io/github/license/Eugen417/GTC_VENTMACHINE_HA.svg?style=for-the-badge)](https://github.com/Eugen417/GTC_VENTMACHINE_HA/blob/main/LICENSE)

<p align="center">
  <a href="README.md">🇷🇺 Русский</a> | <b>🇬🇧 English</b>
</p>

# GTC Ventmachine Integration for Home Assistant

Custom **Home Assistant** integration for controlling **Ventmachine** supply and heat-recovery ventilation units (**GTC** automation, **Syberia 5 / Oasis v.5** controllers) over **Modbus TCP**.

<p align="center">
  <img width="220" height="220" alt="GTC Ventmachine Modbus" src="custom_components/gtc_ventmachine/brand/logo.png" />
</p>

---

## 📥 Installation & Setup

> **⚠️ IMPORTANT:**
> 1. Before installing this integration, **remove or comment out any legacy YAML Modbus configuration** for this ventilation unit in Home Assistant (`configuration.yaml` / `packages`).
> 2. **Close the GTC mobile app**: the onboard controller supports **only one active Modbus TCP connection at a time**. If an older YAML config or the mobile app holds the port open, the controller will reject incoming connections (`Connection refused`).

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Eugen417&repository=GTC_VENTMACHINE_HA&category=Integration)

1. **HACS**: Click the button above or add `https://github.com/Eugen417/GTC_VENTMACHINE_HA` under *Custom Repositories* as category **Integration**.
2. **Restart**: Restart Home Assistant after downloading the integration.
3. **Add Device**: Go to *Settings → Devices & Services → Add Integration*, search for **GTC Ventmachine**, and enter:
   * **IP address or hostname** of the controller (or RS-485 gateway).
   * **Modbus TCP port** (default `502`).
   * **Slave ID (Device address)** (default `1` — must match the Modbus address configured on the wall panel).
4. **Reconfigure Options**: You can update the IP address, port, or Slave ID at any time via the **Configure** button on the integration card without removing the device.

---

## ✨ Key Features (v1.3.6)

* **Native Control Entities**: Full-featured `Climate` and `Fan` entities for standard Home Assistant dashboards, Apple HomeKit, and Yandex Smart Home (with instant UI feedback and real-time `hvac_action` reporting).
* **Independent Supply & Exhaust Fan Control**: Dedicated `Supply fan speed` (register `32`) and `Exhaust fan speed` (register `33`) sliders for heat-recovery ventilation (HRV) units. Disabled by default so supply-only systems stay uncluttered — enable in one click from entity settings.
* **Reliable Modbus TCP Transport**: Reads write acknowledgments (`0x06`), applies `30 ms` inter-frame spacing for RS-485 gateways, and supports legacy controller firmware (`0.95` / `0.102`, `Transaction ID = 0`).
* **Automatic Hardware Detection**: Reads controller firmware version, MAC address, and installed hardware configuration (`Type_Dev`: heater type, cooler/condensing unit, and heat exchanger) on startup.
* **Long-Term Home Assistant Statistics**: All numeric sensors define proper `device_class` and `state_class: measurement` for long-term history graphs.
* **Semantic Alarm Reporting**: All 21 fault/alarm binary sensors use `device_class: problem` with native Home Assistant localization and history coloring.
* **Bilingual UI & Documentation**: Full English and Russian localization (`translations/en.json`, `translations/ru.json`).

---

## 🌐 Entity Reference

### 🎛️ Controls (`climate`, `fan`, `number`, `select`)

| Entity | Platform | Icon | Description & Range |
| --- | --- | --- | --- |
| **Climate** | `climate` | `mdi:thermostat` | Main thermostat: Heat / Off, target temperature (`5.0–30.0 °C`, step `0.5 °C`), and fan speed (`1–10`) |
| **GTC Fan** | `fan` | `mdi:fan` | Fan control: On / Off, speeds `1–10` (`10–100%`) |
| **Target Temperature** | `number` | `mdi:thermometer-check` | Direct target temperature input (`5.0–30.0 °C`, step `0.5 °C`, reg. `31`) |
| **Supply fan speed** | `number` | `mdi:fan-chevron-up` | Supply fan speed slider (`1–10`, reg. `32`, disabled by default) |
| **Exhaust fan speed** | `number` | `mdi:fan-chevron-down` | Exhaust fan speed slider (`1–10`, reg. `33`, disabled by default) |
| **System poll interval** | `select` | `mdi:timer-cog` | Modbus polling interval (`2–10` seconds, persisted across restarts) |

### 🌡️ Sensors (`sensor`)

| Entity | Icon | Default | Description & Units |
| --- | --- | --- | --- |
| **Unit State** | `mdi:state-machine` | Enabled | Current operating stage (*Standby*, *Running*, *Damper Opening*, *Preheating*, *Northern Start*, *Coast-down*, etc.) |
| **Supply Temperature (T1)** | `mdi:thermometer` | Enabled | Supply duct air temperature sensor T1 (`°C`) |
| **Target Temperature** | `mdi:thermometer-check` | Enabled | Active temperature setpoint (`°C`) |
| **Outdoor Temperature (T3)** | `mdi:thermometer` | Enabled | Outdoor intake air temperature sensor T3 (`°C`) |
| **Return Water Temperature (T2)** | `mdi:coolant-temperature` | Disabled* | Return water temperature sensor T2 for hydronic heaters (`°C`) |
| **Room Temperature** | `mdi:home-thermometer` | Enabled | Wall-panel indoor temperature sensor (`°C`) |
| **Room Humidity** | `mdi:water-percent` | Enabled | Indoor relative humidity (`%`) |
| **Current Supply / Exhaust Speed** | `mdi:fan-speed-1` / `mdi:fan-speed-3` | En / Dis* | Actual fan speed stage (`0–10`) |
| **Target Supply / Exhaust Speed** | `mdi:fan-speed-2` | En / Dis* | Configured fan speed stage (`1–10`) |
| **Filter Contamination** | `mdi:air-filter` | Enabled | Filter 1 fouling level (`0–100%`) |
| **Fan 1 / 2 RPM** | `mdi:fan` | Disabled* | Motor rotational speed (`RPM`) |
| **Operation Timer** | `mdi:timer-sand` | Enabled | Countdown timer for transitional stages (`MM:SS`) |
| **Next Schedule Timer** | `mdi:calendar-clock` | Enabled | Time, temperature, and fan speed of the next scheduled event |

*\*Entities marked "Disabled" are created disabled by default to keep the dashboard clean and can be enabled at any time from device entity settings in Home Assistant.*

### ⚙️ Process Statuses & ⚠️ Alarms (`binary_sensor`, class `problem`)

* **Diagnostic Process Sensors**: *Power*, *Transition Active*, *Heating Available*, *Damper Opening/Closing*, *Preheating*, *Northern Start*, *Rotor Spin-Up*, *Fan Start/Coast-Down*, *Hot/Chilled Water Valves*, *Panel External Lock*.
* **Safety, Mechanical & Sensor Faults (`binary_sensor`)**: *Fire Alarm*, *Heater Overheat*, *System Overheat / Underheat*, *Water / Air / Capillary / Heat-Exchanger Freeze Risk*, *Fan 1 / 2 Fault*, *Filter 1 / 2 100%*, *No Heat Carrier*, *Condensing Unit 1 / 2 Pressure*, *Sensors T1–T5 & Preheater Sensor Faults*.

---

## 🔌 Connection Recommendations (Onboard Ethernet vs. RS-485 Gateway)

The integration supports two ways of connecting to the GTC controller:
1. **Via the controller's onboard Ethernet port** (TCP port `502`).
2. **Via an external RS-485 ↔ Wi-Fi / Ethernet gateway** in *Modbus TCP ↔ Modbus RTU* converter mode — for example:
   * Industrial modem **[Promodem WiFi-485 AC (PRO271.01)](https://promodem.ru/produkty/s-interfeysom-rs-485/modem-promodem-wifi-485-ac.html)** (mounts inside the ventilation unit enclosure with 220 V AC power).
   * **Elfin E11 (Ethernet)** / **Elfin EW11 (Wi-Fi)** converters.

> **💡 Practical Tip:** If the onboard Ethernet interface occasionally stops responding or drops TCP sessions, connecting an external **Modbus RTU-TCP** gateway (Promodem or Elfin) to the controller's **RS-485** terminal block provides rock-solid 24/7 operation.

---

## 🤖 Automations (Blueprints)

A ready-to-use Home Assistant Blueprint is available for automatic **CO2-based ventilation control** (automatically turns the unit on/off and adjusts fan speed based on indoor CO2 concentration):

[![Open your Home Assistant instance and show the blueprint import dialog with a specific blueprint pre-filled.](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2FEugen417%2Fhomeassistant-blueprints%2Fblob%2Fmain%2Fgtc_co2_fan_speed_on-off.yaml)

[View Blueprint Source Code](https://github.com/Eugen417/homeassistant-blueprints/blob/main/gtc_co2_fan_speed_on-off.yaml)

---

## 📄 License

Distributed under the **MIT License**. See [LICENSE](LICENSE) for details.

**Author:** [@Eugen417](https://github.com/Eugen417)  
**Version:** 1.3.6

