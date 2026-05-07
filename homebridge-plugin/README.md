# homebridge-ambientika

**Apple Home, Google Home & Amazon Alexa integration for Ambientika ventilation units**

This [Homebridge](https://homebridge.io) plugin connects Ambientika ventilation units to Apple HomeKit (and via Homebridge also to Google Home and Amazon Alexa).

Works via the [Ambientika MQTT Bridge](../README.md) – the bridge handles cloud communication, this plugin exposes the devices to HomeKit.

## Features

- Control ventilation mode (Auto, Manual, Night, Standby)
- Adjust fan speed
- Monitor humidity, supply air temperature, air quality
- Filter alarm notification in Home app
- Works with Siri: "Hey Siri, set ventilation to night mode"
- Works with Google Home and Amazon Alexa via Homebridge

## Prerequisites

1. **Homebridge** installed (see [homebridge.io](https://homebridge.io))
2. **Ambientika MQTT Bridge** running and publishing to an MQTT broker
3. **MQTT broker** (e.g. Mosquitto) accessible from your Homebridge host

## Installation

### Via Homebridge UI (recommended)

1. Open the Homebridge UI
2. Go to **Plugins**
3. Search for **homebridge-ambientika**
4. Click **Install**

### Via npm

```bash
npm install -g homebridge-ambientika
```

## Configuration

Add to your Homebridge `config.json`:

```json
{
  "platforms": [
    {
      "platform": "AmbientikaPlugin",
      "name": "Ambientika",
      "mqttHost": "localhost",
      "mqttPort": 1883,
      "mqttUsername": "",
      "mqttPassword": "",
      "topicPrefix": "ambientika"
    }
  ]
}
```

### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `mqttHost` | string | `localhost` | MQTT broker hostname or IP |
| `mqttPort` | number | `1883` | MQTT broker port |
| `mqttUsername` | string | `` | MQTT username (optional) |
| `mqttPassword` | string | `` | MQTT password (optional) |
| `topicPrefix` | string | `ambientika` | MQTT topic prefix (must match bridge config) |

## HomeKit Accessories

Each Ambientika device appears as an **Air Purifier** accessory in the Home app with:

- **Active / Inactive** – turns ventilation on (Auto) or off (Standby)
- **Auto / Manual mode** – switches between sensor-driven and manual control
- **Fan speed** – Low / Medium / High (shown as rotation speed %)
- **Humidity sensor** – current room humidity
- **Temperature sensor** – supply air temperature
- **Air quality sensor** – air quality index (maps to HomeKit levels)
- **Filter maintenance** – shows alert when filter needs service

## Siri Commands

- "Hey Siri, turn on ventilation"
- "Hey Siri, set ventilation to automatic"
- "Hey Siri, what is the humidity in the bedroom?"

## Architecture

```
Ambientika Cloud
      |
      v
Ambientika MQTT Bridge  (Python, polls cloud API)
      |
      v
MQTT Broker  (Mosquitto)
      |
      v
homebridge-ambientika  (this plugin, subscribes to MQTT)
      |
      v
Homebridge  ->  Apple HomeKit / Google Home / Amazon Alexa
```

## License

MIT
