# Ambientika MQTT Bridge – Home Assistant Add-on

MQTT bridge for Ambientika ventilation units. Connects the Ambientika Cloud API to your local MQTT broker with Home Assistant Auto-Discovery support.

See the top-level [`ha-addon/README.md`](../ha-addon/README.md) for full installation and configuration instructions.

## Quick install

1. In Home Assistant, go to **Settings → Add-ons → Add-on Store**.
2. Open the three-dot menu (top right) → **Repositories** and add the URL `https://github.com/ambientika-eu/ambientika-mqtt-bridge`.
3. Install **Ambientika MQTT Bridge** from the store.
4. In the add-on **Configuration** tab, enter your Ambientika username and password (plus MQTT credentials if your broker requires authentication).
5. Start the add-on. Your devices will appear automatically under **Settings → Devices & Services → MQTT**.
