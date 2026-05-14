# Ambientika MQTT Bridge – Home Assistant Add-on

This folder contains the Home Assistant OS (HAOS) Add-on for the Ambientika MQTT Bridge.

With this add-on, you can install the Ambientika MQTT Bridge directly from the Home Assistant Add-on Store with a single click – no Docker, no terminal, no Raspberry Pi setup required.

## Installation

### Method 1: Add Repository to Home Assistant (Recommended)

1. In Home Assistant, go to **Settings > Add-ons > Add-on Store**
2. Click the **three-dot menu** (top right) > **Repositories**
3. Add this URL:
   ```
      https://github.com/ambientika-eu/ambientika-mqtt-bridge
   ```
4. Click **Add**, then close the dialog
5. Search for **"Ambientika MQTT Bridge"** in the store
6. Click **Install**

### Method 2: Manual Installation

1. Copy the `ha-addon` folder contents to your HA config directory:
   ```
   /config/addons/ambientika_mqtt_bridge/
   ```
2. Restart Home Assistant
3. The add-on appears under **Settings > Add-ons > Local Add-ons**

---

## Configuration

After installation, configure the add-on via the **Configuration** tab:

| Option | Description | Default |
|--------|-------------|---------|
| `ambientika_username` | Your Ambientika account email | *(required)* |
| `ambientika_password` | Your Ambientika account password | *(required)* |
| `mqtt_host` | MQTT broker hostname | `core-mosquitto` |
| `mqtt_port` | MQTT broker port | `1883` |
| `mqtt_username` | MQTT username (**required** for most brokers) | `` |
| `mqtt_password` | MQTT password (**required** for most brokers) | `` |
| `mqtt_topic_prefix` | MQTT topic prefix | `ambientika` |
| `poll_interval` | Polling interval in seconds | `30` |
| `log_level` | Log verbosity | `INFO` |

> **MQTT credentials are required for most brokers.** The official Home Assistant Mosquitto add-on and most production setups disable anonymous MQTT access. If `mqtt_username` / `mqtt_password` are empty the bridge cannot connect (`Not authorized`). Create a dedicated MQTT user for the bridge (e.g. via the Mosquitto add-on's `logins` option) and set both fields. Only leave them empty if you have explicitly configured your broker to allow anonymous access.
>
> **Note:** If you use the official **Mosquitto broker** add-on, the default `core-mosquitto` hostname works out of the box.

---

## Home Assistant Auto-Discovery

The bridge publishes MQTT Auto-Discovery messages, so your Ambientika devices appear automatically in Home Assistant under:

**Settings > Devices & Services > MQTT > Devices**

The following entities are created per device:

### Sensors
- Humidity (%)
- Supply Air Temperature (°C)
- Extract Air Temperature (°C)
- Outdoor Temperature (°C)
- Air Quality Index
- Fan Speed (numeric)
- Heat Recovery Efficiency (%)
- Power Consumption (W)

### Binary Sensors
- Filter Alarm
- Defrost Active

### Select / Control Entities
- Operating Mode (Auto, ManualLow, ManualMedium, ManualHigh, Night, Standby, Away, Boost)
- Fan Speed (Low, Medium, High)
- Humidity Setpoint (40–90%)

---

## Example Automations

### Boost when humidity spikes

```yaml
automation:
  - alias: "Ambientika Humidity Boost"
    trigger:
      - platform: numeric_state
        entity_id: sensor.ambientika_humidity
        above: 75
    action:
      - service: select.select_option
        target:
          entity_id: select.ambientika_operating_mode
        data:
          option: ManualHigh
```

### Night mode on schedule

```yaml
automation:
  - alias: "Ambientika Night Mode"
    trigger:
      - platform: time
        at: "22:00:00"
    action:
      - service: select.select_option
        target:
          entity_id: select.ambientika_operating_mode
        data:
          option: Night
  - alias: "Ambientika Day Mode"
    trigger:
      - platform: time
        at: "07:00:00"
    action:
      - service: select.select_option
        target:
          entity_id: select.ambientika_operating_mode
        data:
          option: Auto
```

### Filter alarm notification

```yaml
automation:
  - alias: "Ambientika Filter Alarm"
    trigger:
      - platform: state
        entity_id: binary_sensor.ambientika_filter_alarm
        to: "on"
    action:
      - service: notify.mobile_app
        data:
          title: "Ambientika Filter Service"
          message: "Please replace or clean the ventilation filter."
```

---

## MQTT Topics

See the [main README](../README.md#mqtt-topics) for the complete topic list.

---

## Support

- GitHub Issues: https://github.com/ambientika-eu/ambientika-mqtt-bridge/issues
- Ambientika website: https://www.ambientika.eu
