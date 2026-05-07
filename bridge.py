#!/usr/bin/env python3
"""
Ambientika MQTT Bridge
Connects Ambientika Cloud API to any MQTT broker.
Home Assistant Auto-Discovery | ioBroker | openHAB | Loxone | Node-RED
"""
import asyncio
import json
import logging
import os
import signal
import sys
from typing import Optional

import paho.mqtt.client as mqtt
import yaml

try:
    from ambientika_py import AmbientikaAPI, Device
    from ambientika_py.models import OperatingMode, FanSpeed, HumidityLevel
except ImportError:
    print("ERROR: ambientika_py not installed. Run: pip install ambientika_py")
    sys.exit(1)

log = logging.getLogger("ambientika_bridge")


class BridgeConfig:
    def __init__(self):
        self.username = ""
        self.password = ""
        self.host = "https://app.ambientika.eu:4521"
        self.mqtt_host = "localhost"
        self.mqtt_port = 1883
        self.mqtt_user = ""
        self.mqtt_pass = ""
        self.mqtt_client_id = "ambientika-bridge"
        self.mqtt_tls = False
        self.topic_prefix = "ambientika"
        self.discovery_prefix = "homeassistant"
        self.enable_discovery = True
        self.poll_interval = 30
        self.log_level = "INFO"

    @classmethod
    def from_yaml(cls, path: str) -> "BridgeConfig":
        with open(path) as f:
            raw = yaml.safe_load(f)
        cfg = cls()
        amb = raw.get("ambientika", {})
        cfg.username = os.environ.get("AMBIENTIKA_USER", amb.get("username", ""))
        cfg.password = os.environ.get("AMBIENTIKA_PASS", amb.get("password", ""))
        cfg.host = amb.get("host", cfg.host)
        mq = raw.get("mqtt", {})
        cfg.mqtt_host = os.environ.get("MQTT_HOST", mq.get("host", cfg.mqtt_host))
        cfg.mqtt_port = int(os.environ.get("MQTT_PORT", mq.get("port", cfg.mqtt_port)))
        cfg.mqtt_user = os.environ.get("MQTT_USER", mq.get("username", ""))
        cfg.mqtt_pass = os.environ.get("MQTT_PASS", mq.get("password", ""))
        cfg.mqtt_tls = mq.get("tls", False)
        br = raw.get("bridge", {})
        cfg.topic_prefix = br.get("topic_prefix", cfg.topic_prefix)
        cfg.discovery_prefix = br.get("discovery_prefix", cfg.discovery_prefix)
        cfg.enable_discovery = br.get("enable_discovery", True)
        cfg.poll_interval = int(br.get("poll_interval", cfg.poll_interval))
        cfg.log_level = br.get("log_level", cfg.log_level)
        return cfg


def state_topic(prefix, serial): return f"{prefix}/{serial}/state"
def avail_topic(prefix, serial): return f"{prefix}/{serial}/availability"
def cmd_topic(prefix, serial, attr): return f"{prefix}/{serial}/set/{attr}"
def attr_topic(prefix, serial, attr): return f"{prefix}/{serial}/{attr}"


def build_discovery_configs(cfg, serial, device_name):
    device_info = {"identifiers": [serial], "name": device_name,
                   "manufacturer": "Ambientika / SUEDWIND", "model": "Smart Ventilation Unit"}
    base = cfg.discovery_prefix
    prefix = cfg.topic_prefix
    avail = avail_topic(prefix, serial)
    state = state_topic(prefix, serial)
    entities = []
    for key, name, unit, dc, icon in [
        ("temperature","Temperature","\u00b0C","temperature",None),
        ("humidity","Humidity","%","humidity",None),
        ("air_quality","Air Quality",None,None,"mdi:air-filter"),
        ("filters_status","Filter Status",None,None,"mdi:air-filter"),
        ("operating_mode","Mode",None,None,"mdi:fan"),
        ("fan_speed","Fan Speed",None,None,"mdi:speedometer"),
        ("humidity_level","Humidity Level",None,None,"mdi:water-percent"),
        ("device_role","Device Role",None,None,"mdi:information"),
    ]:
        p = {"name":name,"unique_id":f"ambientika_{serial}_{key}",
             "state_topic":state,"value_template":f"{{{{ value_json.{key} }}}}",
             "availability_topic":avail,"device":device_info}
        if unit: p["unit_of_measurement"] = unit
        if dc: p["device_class"] = dc
        if icon: p["icon"] = icon
        entities.append((f"{base}/sensor/{serial}_{key}/config", p))
    for key, name, dc in [("humidity_alarm","Humidity Alarm","moisture"),("night_alarm","Night Alarm","problem")]:
        p = {"name":name,"unique_id":f"ambientika_{serial}_{key}",
             "state_topic":state,"value_template":f"{{{{ value_json.{key} }}}}",
             "payload_on":"True","payload_off":"False","availability_topic":avail,"device":device_info,"device_class":dc}
        entities.append((f"{base}/binary_sensor/{serial}_{key}/config", p))
    for key, name, opts, icon in [
        ("operating_mode","Mode",[m.value for m in OperatingMode],"mdi:fan"),
        ("fan_speed","Fan Speed",[s.value for s in FanSpeed],"mdi:speedometer"),
        ("humidity_level","Humidity Level",[h.value for h in HumidityLevel],"mdi:water-percent"),
    ]:
        p = {"name":name,"unique_id":f"ambientika_{serial}_{key}_select",
             "state_topic":state,"value_template":f"{{{{ value_json.{key} }}}}",
             "command_topic":cmd_topic(prefix,serial,key),"options":opts,
             "availability_topic":avail,"device":device_info,"icon":icon}
        entities.append((f"{base}/select/{serial}_{key}/config", p))
    return entities


class Ambientikabridge:
    def __init__(self, cfg: BridgeConfig):
        self.cfg = cfg
        self.api: Optional[AmbientikaAPI] = None
        self.devices = []
        self._running = False
        self._mqtt_connected = False
        self._fail_count = {}
        self.mqttc = mqtt.Client(client_id=cfg.mqtt_client_id, protocol=mqtt.MQTTv5)
        if cfg.mqtt_user:
            self.mqttc.username_pw_set(cfg.mqtt_user, cfg.mqtt_pass)
        if cfg.mqtt_tls:
            self.mqttc.tls_set()
        self.mqttc.on_connect = self._on_connect
        self.mqttc.on_disconnect = self._on_disconnect
        self.mqttc.on_message = self._on_message
        self.mqttc.will_set(f"{cfg.topic_prefix}/bridge/availability", "offline", qos=1, retain=True)

    def _on_connect(self, client, userdata, flags, rc, props=None):
        if rc == 0:
            log.info("MQTT connected")
            self._mqtt_connected = True
            for dev in self.devices:
                for attr in ("operating_mode", "fan_speed", "humidity_level"):
                    client.subscribe(cmd_topic(self.cfg.topic_prefix, dev.serial_number, attr))
            client.publish(f"{self.cfg.topic_prefix}/bridge/availability", "online", qos=1, retain=True)
        else:
            log.error("MQTT connect failed rc=%s", rc)

    def _on_disconnect(self, client, userdata, rc, props=None):
        log.warning("MQTT disconnected rc=%s", rc)
        self._mqtt_connected = False

    def _on_message(self, client, userdata, msg):
        topic = msg.topic
        payload = msg.payload.decode("utf-8", errors="replace").strip()
        for dev in self.devices:
            for attr in ("operating_mode", "fan_speed", "humidity_level"):
                if topic == cmd_topic(self.cfg.topic_prefix, dev.serial_number, attr):
                    asyncio.run_coroutine_threadsafe(self._apply_command(dev, attr, payload), self._loop)

    async def _apply_command(self, dev, attr, value):
        try:
            if attr == "operating_mode":
                await dev.change_mode(operating_mode=OperatingMode(value))
            elif attr == "fan_speed":
                await dev.change_mode(fan_speed=FanSpeed(value))
            elif attr == "humidity_level":
                await dev.change_mode(humidity_level=HumidityLevel(value))
            log.info("Applied %s=%s to %s", attr, value, dev.serial_number)
            await asyncio.sleep(1)
            await self._poll_device(dev)
        except Exception as e:
            log.error("Command failed: %s", e)

    async def _poll_device(self, dev):
        serial = dev.serial_number
        try:
            status = await dev.get_status()
            payload = {}
            for k in ("temperature","humidity","air_quality","filters_status","operating_mode",
                      "fan_speed","humidity_level","device_role","humidity_alarm","night_alarm"):
                v = getattr(status, k, None)
                payload[k] = v.value if hasattr(v, "value") else str(v) if v is not None else ""
            self._fail_count[serial] = 0
            self.mqttc.publish(state_topic(self.cfg.topic_prefix, serial), json.dumps(payload), qos=0, retain=True)
            for k, v in payload.items():
                self.mqttc.publish(attr_topic(self.cfg.topic_prefix, serial, k), str(v), qos=0, retain=True)
            self.mqttc.publish(avail_topic(self.cfg.topic_prefix, serial), "online", qos=1, retain=True)
        except Exception as e:
            self._fail_count[serial] = self._fail_count.get(serial, 0) + 1
            log.warning("Poll failed for %s (%d): %s", serial, self._fail_count[serial], e)
            if self._fail_count[serial] >= 3:
                await self._re_auth()

    async def _re_auth(self):
        try:
            await self.api.login(self.cfg.username, self.cfg.password)
            self.devices = await self.api.get_devices()
            log.info("Re-auth OK, %d devices", len(self.devices))
        except Exception as e:
            log.error("Re-auth failed: %s", e)

    def _publish_discovery(self):
        if not self.cfg.enable_discovery:
            return
        for dev in self.devices:
            serial = dev.serial_number
            name = getattr(dev, "name", serial) or serial
            for topic, payload in build_discovery_configs(self.cfg, serial, name):
                self.mqttc.publish(topic, json.dumps(payload), qos=1, retain=True)

    async def run(self):
        logging.basicConfig(level=getattr(logging, self.cfg.log_level.upper(), logging.INFO),
                            format="%(asctime)s %(levelname)-8s %(name)s: %(message)s")
        log.info("Ambientika MQTT Bridge starting...")
        self._loop = asyncio.get_event_loop()
        self.api = AmbientikaAPI(host=self.cfg.host)
        await self.api.login(self.cfg.username, self.cfg.password)
        self.devices = await self.api.get_devices()
        log.info("Found %d device(s)", len(self.devices))
        self.mqttc.connect_async(self.cfg.mqtt_host, self.cfg.mqtt_port)
        self.mqttc.loop_start()
        for _ in range(30):
            if self._mqtt_connected:
                break
            await asyncio.sleep(1)
        if not self._mqtt_connected:
            log.error("MQTT connect timeout")
            sys.exit(1)
        self._publish_discovery()
        self._running = True
        while self._running:
            for dev in self.devices:
                await self._poll_device(dev)
            await asyncio.sleep(self.cfg.poll_interval)

    def stop(self):
        log.info("Stopping bridge...")
        self._running = False
        self.mqttc.publish(f"{self.cfg.topic_prefix}/bridge/availability", "offline", qos=1, retain=True)
        self.mqttc.disconnect()
        self.mqttc.loop_stop()


def main():
    config_path = os.environ.get("CONFIG_PATH", "config.yaml")
    if not os.path.exists(config_path):
        print(f"Config not found: {config_path}")
        print("Copy config.example.yaml to config.yaml and fill in your credentials.")
        sys.exit(1)
    cfg = BridgeConfig.from_yaml(config_path)
    bridge = Ambientikabridge(cfg)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, bridge.stop)
        except (NotImplementedError, RuntimeError):
            pass
    try:
        loop.run_until_complete(bridge.run())
    except KeyboardInterrupt:
        bridge.stop()
    finally:
        loop.close()


if __name__ == "__main__":
    main()
