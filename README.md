# Ambientika MQTT Bridge

MQTT-Bridge fuer Ambientika Lueftungsgeraete – verbindet die Ambientika Cloud API mit jedem MQTT-Broker.

## Unterstuetzte Plattformen

- **Home Assistant** (Auto-Discovery)
- **ioBroker** (MQTT-Adapter mit HA-Discovery-Modus)
- **openHAB** (MQTT-Things-Plugin)
- **Loxone** (virtuelle Ein-/Ausgaenge)
- **Node-RED**, **FHEM**, **Domoticz**, **Grafana/InfluxDB**

## Voraussetzungen

- Python 3.11+
- MQTT-Broker (z.B. Mosquitto)
- Ambientika-Zugangsdaten (App-Account)

## Installation

```bash
git clone https://github.com/martinsaxalber-oss/ambientika-mqtt-bridge.git
cd ambientika-mqtt-bridge
pip install -r requirements.txt
cp config.example.yaml config.yaml
# config.yaml anpassen
python bridge.py
```

## Docker

```bash
cp config.example.yaml config.yaml
# config.yaml anpassen
docker compose up -d
```

## MQTT-Topics

| Topic | Beschreibung |
|-------|-------------|
| `ambientika/<serial>/state` | JSON-State (alle Werte) |
| `ambientika/<serial>/temperature` | Temperatur in Grad C |
| `ambientika/<serial>/humidity` | Luftfeuchtigkeit in % |
| `ambientika/<serial>/air_quality` | Luftqualitaetsindex |
| `ambientika/<serial>/set/operating_mode` | Modus setzen |
| `ambientika/<serial>/set/fan_speed` | Lueftergeschwindigkeit setzen |

## Konfiguration

Siehe `config.example.yaml`.

## Lizenz

MIT License – freie Verwendung und Weitergabe.
