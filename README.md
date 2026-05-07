# Ambientika MQTT Bridge

**MQTT bridge for Ambientika ventilation units** – connects the Ambientika Cloud API to any local MQTT broker with full Home Assistant Auto-Discovery support.

> Works with: Home Assistant · Apple Home · Google Home · Amazon Alexa · Node-RED · Loxone · ioBroker · openHAB · Homey · and any MQTT-capable platform

---

## Supported Platforms

| Platform | Integration | Status |
|----------|-------------|--------|
| **Home Assistant** | MQTT Auto-Discovery (built-in) | Ready |
| **Apple Home** | Homebridge plugin | Ready |
| **Google Home** | Homebridge plugin | Ready |
| **Amazon Alexa** | Homebridge plugin | Ready |
| **Node-RED** | Example flow | Ready |
| **Loxone** | MQTT Virtual I/O guide | Ready |
| **ioBroker** | MQTT adapter | Ready |
| **openHAB** | MQTT binding | Ready |
| **Homey** | MQTT app | Ready |

---

## Architecture

```
Ambientika Cloud API (app.ambientika.eu:4521)
              |
              v
   Ambientika MQTT Bridge   <-- this repository
              |
              v
        MQTT Broker
        (Mosquitto)
       /     |      \
      v      v       v
 Home    Node-RED  Loxone
Assistant          Miniserver
      |
      v
 Apple Home /
 Google Home /
 Amazon Alexa
 (via Homebridge)
```

---

## Quick Start

### Option 1: Docker (recommended)

```bash
git clone https://github.com/martinsaxalber-oss/ambientika-mqtt-bridge.git
cd ambientika-mqtt-bridge
cp config.example.yaml config.yaml
# Edit config.yaml with your credentials
docker-compose up -d
```

### Option 2: Python (manual)

```bash
pip install -r requirements.txt
cp config.example.yaml config.yaml
# Edit config.yaml
python bridge.py
```

### Option 3: Home Assistant Add-on

1. In HA go to Settings > Add-ons > Add-on Store
2. Add repository: `https://github.com/martinsaxalber-oss/ambientika-mqtt-bridge`
3. Install "Ambientika MQTT Bridge" and configure credentials

---

## Configuration

Edit `config.yaml`:

```yaml
ambientika:
  username: "your@email.com"
  password: "yourpassword"

mqtt:
  host: "localhost"
  port: 1883
  topic_prefix: "ambientika"

bridge:
  poll_interval: 30
```

---

## MQTT Topics

All topics use the format: `{prefix}/{serial}/{property}`

### State Topics (published by bridge)

| Topic | Type | Description |
|-------|------|-------------|
| `ambientika/{serial}/state` | JSON | Full device state |
| `ambientika/{serial}/operating_mode` | string | Current mode |
| `ambientika/{serial}/fan_speed` | string | Fan speed |
| `ambientika/{serial}/humidity` | number | Humidity % |
| `ambientika/{serial}/supply_air_temperature` | number | Supply air temp °C |
| `ambientika/{serial}/extract_air_temperature` | number | Extract air temp °C |
| `ambientika/{serial}/outdoor_temperature` | number | Outdoor temp °C |
| `ambientika/{serial}/air_quality` | number | Air quality index |
| `ambientika/{serial}/heat_recovery_efficiency` | number | HRV efficiency % |
| `ambientika/{serial}/power_consumption` | number | Power W |
| `ambientika/{serial}/filter_alarm` | bool | Filter needs service |
| `ambientika/{serial}/defrost_active` | bool | Defrost active |
| `ambientika/{serial}/humidity_setpoint` | number | Humidity target % |

### Command Topics (subscribe to control)

| Topic | Values | Description |
|-------|--------|-------------|
| `ambientika/{serial}/set/operating_mode` | Auto, ManualLow, ManualMedium, ManualHigh, Night, Standby, Away, Boost | Set mode |
| `ambientika/{serial}/set/fan_speed` | Low, Medium, High | Set fan speed |
| `ambientika/{serial}/set/humidity_setpoint` | 40–90 | Set humidity target |

---

## Platform-Specific Guides

- **Node-RED**: See [examples/node-red/README.md](examples/node-red/README.md)
- **Loxone**: See [examples/loxone/README.md](examples/loxone/README.md)
- **Home Assistant Add-on**: See [ha-addon/README.md](ha-addon/README.md)
- **Apple Home / Google Home / Alexa (Homebridge)**: See [homebridge-plugin/README.md](homebridge-plugin/README.md)

---

## Home Assistant Auto-Discovery

When the bridge starts, it publishes MQTT Auto-Discovery messages. Your Ambientika devices appear automatically under **Settings > Devices & Services > MQTT**.

Entities created per device:
- 8 sensors (humidity, temperatures, air quality, efficiency, power, fan speed)
- 2 binary sensors (filter alarm, defrost)
- 3 select controls (operating mode, fan speed, humidity setpoint)

---

## Requirements

- Ambientika account (app.ambientika.eu)
- MQTT broker (Mosquitto recommended)
- Python 3.11+ or Docker

---

## Links

- Ambientika website: https://www.ambientika.eu
- Existing Home Assistant integration: https://github.com/lipkau/HomeAssistant-integration-for-Ambientika
- Issues / Feature requests: https://github.com/martinsaxalber-oss/ambientika-mqtt-bridge/issues

---

## License

MIT
