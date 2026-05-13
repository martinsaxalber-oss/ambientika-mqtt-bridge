# Ambientika MQTT Bridge

**MQTT bridge for Ambientika ventilation units** – connects the Ambientika Cloud API to any local MQTT broker with full Home Assistant Auto-Discovery support.

> Works with: Home Assistant · Apple Home · Google Home · Amazon Alexa · Node-RED · Loxone · ioBroker · Matter · openHAB · Homey · and any MQTT-capable platform

---

## Supported Platforms

| Platform | Integration | Folder | Status |
|----------|-------------|--------|--------|
| **Home Assistant** | MQTT Auto-Discovery + Add-on | `ha-addon/` | ✅ Ready |
| **Apple Home** | Homebridge plugin | `homebridge-plugin/` | ✅ Ready |
| **Apple Home (native)** | Matter Bridge | `matter-bridge/` | ✅ Ready |
| **Google Home** | Homebridge plugin / Matter | `homebridge-plugin/` · `matter-bridge/` | ✅ Ready |
| **Amazon Alexa** | Homebridge plugin / Matter | `homebridge-plugin/` · `matter-bridge/` | ✅ Ready |
| **Node-RED** | Example flow | `examples/node-red/` | ✅ Ready |
| **Loxone** | MQTT Virtual I/O guide | `examples/loxone/` | ✅ Ready |h
| **ioBroker** | Native adapter | `iobroker-adapter/` | ✅ Ready |
| **SmartThings** | Matter Bridge | `matter-bridge/` | ✅ Ready |
| **openHAB** | MQTT Binding (generic) | See README | 📖 Guide |
| **KNX / BACnet** | Via MQTT-KNX gateway | See README | 📖 Guide |

---

## Quick Start

```bash
git clone https://github.com/ambientika-eu/ambientika-mqtt-bridge.git
cd ambientika-mqtt-bridge
cp .env.example .env
# Edit .env with your Ambientika credentials and MQTT broker settings
docker compose up -d
```

---

## Architecture
```
Ambientika Device (WiFi)
       |  (HTTPS/WebSocket)
  [Ambientika MQTT Bridge]  ← this project
       |  (MQTT)
  [MQTT Broker]
       |
   ┌───┴────────────────────────────────────┐
   │                                         │
   ▼                                         ▼
[Home Assistant]                    [Matter Bridge]
[Node-RED]                          [Apple Home]
[ioBroker]                          [Google Home]
[Loxone]                            [Amazon Alexa]
[openHAB]                           [SmartThings]
[Homebridge → Apple/Google/Alexa]
```

---

## Integration Guides

### Home Assistant Add-on
See [`ha-addon/README.md`](ha-addon/README.md)

### Apple Home + Google Home + Alexa (Homebridge)
See [`homebridge-plugin/README.md`](homebridge-plugin/README.md)

### Apple Home + Google Home + Alexa + SmartThings (Matter – native, no bridge app needed)
See [`matter-bridge/README.md`](matter-bridge/README.md)

### Node-RED
See [`examples/node-red/README.md`](examples/node-red/README.md)

### Loxone
See [`examples/loxone/README.md`](examples/loxone/README.md)

### ioBroker
See [`iobroker-adapter/README.md`](iobroker-adapter/README.md)

---

## MQTT Topics

| Topic | Direction | Description |
|-------|-----------|-------------|
| `ambientika/<deviceId>/status` | Bridge → Broker | Full device state (JSON) |
| `ambientika/<deviceId>/set` | Broker → Bridge | Set mode/fanSpeed (JSON) |
| `ambientika/<deviceId>/availability` | Bridge → Broker | `online` / `offline` |

### Status Payload Example

```json
{
  "deviceId": "DEV001",
  "serial": "AMB-2024-001",
  "name": "Bedroom",
  "mode": "HRV",
  "fanSpeed": 75,
  "temperature": 21.5,
  "humidity": 52,
  "airQuality": 850,
  "filterAlarm": false,
  "online": true,
  "rssi": -58
}
```

### Command Payload Example

```json
{ "mode": "NIGHT" }
{ "fanSpeed": 50 }
{ "mode": "HRV", "fanSpeed": 75 }
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `AMBIENTIKA_EMAIL` | — | Ambientika account email |
| `AMBIENTIKA_PASSWORD` | — | Ambientika account password |
| `MQTT_BROKER` | `localhost` | MQTT broker host |
| `MQTT_PORT` | `1883` | MQTT broker port |
| `MQTT_USER` | *(empty)* | MQTT username |
| `MQTT_PASSWORD` | *(empty)* | MQTT password |
| `MQTT_PREFIX` | `ambientika` | MQTT topic prefix |
| `POLL_INTERVAL` | `30` | Device poll interval in seconds |
| `HA_DISCOVERY` | `true` | Enable Home Assistant Auto-Discovery |
| `LOG_LEVEL` | `INFO` | Logging level |

---

## Notes

### `ambientika_py` dependency

This project currently installs the [`ambientika_py`](https://github.com/wingertge/ambientika-py) library directly from its upstream Git repository, pinned to a specific commit, because the latest PyPI release (0.0.5) does not yet contain the `LightSensorLevel` enum required by the bridge. This is a temporary workaround – see [#3](https://github.com/ambientika-eu/ambientika-mqtt-bridge/issues/3) and [wingertge/ambientika-py#8](https://github.com/wingertge/ambientika-py/issues/8) for tracking. Building from source therefore requires `git` to be available inside the build environment (already handled in the provided `Dockerfiles`).

---

## License

MIT License – © Ambientika / SUEDWIND

---

## Links

- 🌐 [ambientika.eu](https://www.ambientika.eu)
- 📦 [GitHub Repository](https://github.com/martinsaxalber-oss/ambientika-mqtt-bridge)
