#!/usr/bin/env python3
"""
Ambientika MQTT Bridge

Connects the Ambientika Cloud API to any MQTT broker.
Supports Home Assistant Auto-Discovery as well as ioBroker, openHAB,
Loxone and Node-RED (any MQTT-capable system).

Built on top of the community library 'ambientika_py' by wingertge.
"""

import asyncio
import json
import logging
import os
import signal
import sys
from typing import Any, Optional

import paho.mqtt.client as mqtt
import yaml

try:
    from ambientika_py import (
        authenticate,
        Ambientika,
        Device,
        OperatingMode,
        FanSpeed,
        HumidityLevel,
        LightSensorLevel,
    )
    from returns.result import Success, Failure
except ImportError as exc:
    print(
        "ERROR: required dependency missing. "
        "Run: pip install -r requirements.txt  ({})".format(exc)
    )
    sys.exit(1)

log = logging.getLogger("ambientika_bridge")


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

def _env(*names: str, default: str = "") -> str:
    """Return the first non-empty env var among 'names'.

    Treats the literal strings 'null' and 'None' as empty, because
    HA's bashio::config returns the string "null" for optional fields
    that are not set in options.json.
    """
    for n in names:
        v = os.environ.get(n)
        if v and v.lower() not in ("null", "none"):
            return v
    return default


class BridgeConfig:
    def __init__(self) -> None:
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

    def apply_env_overrides(self) -> None:
        """Override any field with matching env vars (HA add-on uses these)."""
        u = _env("AMBIENTIKA_USERNAME", "AMBIENTIKA_USER")
        if u:
            self.username = u
        p = _env("AMBIENTIKA_PASSWORD", "AMBIENTIKA_PASS")
        if p:
            self.password = p
        h = _env("AMBIENTIKA_HOST")
        if h:
            self.host = h

        mh = _env("MQTT_HOST")
        if mh:
            self.mqtt_host = mh
        mp = _env("MQTT_PORT")
        if mp:
            try:
                self.mqtt_port = int(mp)
            except ValueError:
                pass
        mu = _env("MQTT_USERNAME", "MQTT_USER")
        if mu:
            self.mqtt_user = mu
        mpw = _env("MQTT_PASSWORD", "MQTT_PASS")
        if mpw:
            self.mqtt_pass = mpw

        tp = _env("MQTT_TOPIC_PREFIX", "TOPIC_PREFIX")
        if tp:
            self.topic_prefix = tp
        dp = _env("DISCOVERY_PREFIX")
        if dp:
            self.discovery_prefix = dp
        pi = _env("POLL_INTERVAL")
        if pi:
            try:
                self.poll_interval = int(pi)
            except ValueError:
                pass
        ll = _env("LOG_LEVEL")
        if ll:
            self.log_level = ll

    @classmethod
    def from_yaml(cls, path: str) -> "BridgeConfig":
        with open(path) as f:
            raw = yaml.safe_load(f) or {}
        cfg = cls()

        amb = raw.get("ambientika", {}) or {}
        cfg.username = amb.get("username", "") or ""
        cfg.password = amb.get("password", "") or ""
        cfg.host = amb.get("host", cfg.host)

        mq = raw.get("mqtt", {}) or {}
        cfg.mqtt_host = mq.get("host", cfg.mqtt_host)
        cfg.mqtt_port = int(mq.get("port", cfg.mqtt_port))
        cfg.mqtt_user = mq.get("username", "") or ""
        cfg.mqtt_pass = mq.get("password", "") or ""
        cfg.mqtt_tls = bool(mq.get("tls", False))

        br = raw.get("bridge", {}) or {}
        cfg.topic_prefix = br.get("topic_prefix", cfg.topic_prefix)
        cfg.discovery_prefix = br.get("discovery_prefix", cfg.discovery_prefix)
        cfg.enable_discovery = bool(br.get("enable_discovery", True))
        cfg.poll_interval = int(br.get("poll_interval", cfg.poll_interval))
        cfg.log_level = br.get("log_level", cfg.log_level)

        cfg.apply_env_overrides()
        return cfg

    @classmethod
    def from_ha_options(cls, path: str) -> "BridgeConfig":
        """Read /data/options.json written by Home Assistant Supervisor."""
        with open(path) as f:
            raw = json.load(f)
        cfg = cls()
        cfg.username = raw.get("ambientika_username", raw.get("ambientika_user", "")) or ""
        cfg.password = raw.get("ambientika_password", raw.get("ambientika_pass", "")) or ""
        cfg.host = raw.get("ambientika_host", cfg.host)
        cfg.mqtt_host = raw.get("mqtt_host", cfg.mqtt_host)
        cfg.mqtt_port = int(raw.get("mqtt_port", cfg.mqtt_port))
        cfg.mqtt_user = raw.get("mqtt_username", raw.get("mqtt_user", "")) or ""
        cfg.mqtt_pass = raw.get("mqtt_password", raw.get("mqtt_pass", "")) or ""
        cfg.mqtt_tls = bool(raw.get("mqtt_tls", False))
        cfg.topic_prefix = raw.get("mqtt_topic_prefix", raw.get("topic_prefix", cfg.topic_prefix))
        cfg.discovery_prefix = raw.get("discovery_prefix", cfg.discovery_prefix)
        cfg.enable_discovery = bool(raw.get("enable_discovery", True))
        cfg.poll_interval = int(raw.get("poll_interval", cfg.poll_interval))
        cfg.log_level = raw.get("log_level", cfg.log_level)
        cfg.apply_env_overrides()
        return cfg

    @classmethod
    def from_env(cls) -> "BridgeConfig":
        cfg = cls()
        cfg.apply_env_overrides()
        return cfg


# ---------------------------------------------------------------------------
# Topic helpers
# ---------------------------------------------------------------------------

def state_topic(prefix: str, serial: str) -> str:
    return f"{prefix}/{serial}/state"


def avail_topic(prefix: str, serial: str) -> str:
    return f"{prefix}/{serial}/availability"


def cmd_topic(prefix: str, serial: str, attr: str) -> str:
    return f"{prefix}/{serial}/set/{attr}"


# ---------------------------------------------------------------------------
# Home Assistant Auto-Discovery
# ---------------------------------------------------------------------------

def build_discovery_configs(cfg: BridgeConfig, serial: str, device_name: str):
    device_info = {
        "identifiers": [serial],
        "name": device_name,
        "manufacturer": "Ambientika / SUEDWIND",
        "model": "Smart Ventilation Unit",
    }
    base = cfg.discovery_prefix
    prefix = cfg.topic_prefix
    avail = avail_topic(prefix, serial)
    state = state_topic(prefix, serial)

    entities = []

    sensor_defs = [
        ("temperature", "Temperature", "\u00b0C", "temperature", None),
        ("humidity", "Humidity", "%", "humidity", None),
        ("air_quality", "Air Quality", None, None, "mdi:air-filter"),
        ("filters_status", "Filter Status", None, None, "mdi:air-filter"),
        ("operating_mode", "Mode", None, None, "mdi:fan"),
        ("fan_speed", "Fan Speed", None, None, "mdi:speedometer"),
        ("humidity_level", "Humidity Level", None, None, "mdi:water-percent"),
        ("light_sensor_level", "Light Sensor Level", None, None, "mdi:brightness-5"),
        ("device_role", "Device Role", None, None, "mdi:information"),
    ]
    for key, name, unit, dc, icon in sensor_defs:
        p = {
            "name": name,
            "unique_id": f"ambientika_{serial}_{key}",
            "state_topic": state,
            "value_template": f"{{{{ value_json.{key} }}}}",
            "availability_topic": avail,
            "device": device_info,
        }
        if unit:
            p["unit_of_measurement"] = unit
        if dc:
            p["device_class"] = dc
        if icon:
            p["icon"] = icon
        entities.append((f"{base}/sensor/{serial}_{key}/config", p))

    bin_defs = [
        ("humidity_alarm", "Humidity Alarm", "moisture"),
        ("night_alarm", "Night Alarm", "problem"),
    ]
    for key, name, dc in bin_defs:
        p = {
            "name": name,
            "unique_id": f"ambientika_{serial}_{key}",
            "state_topic": state,
            "value_template": f"{{{{ value_json.{key} }}}}",
            "payload_on": "True",
            "payload_off": "False",
            "availability_topic": avail,
            "device": device_info,
            "device_class": dc,
        }
        entities.append((f"{base}/binary_sensor/{serial}_{key}/config", p))

    select_defs = [
        ("operating_mode", "Mode", [m.name for m in OperatingMode], "mdi:fan"),
        ("fan_speed", "Fan Speed", [s.name for s in FanSpeed], "mdi:speedometer"),
        ("humidity_level", "Humidity Level", [h.name for h in HumidityLevel], "mdi:water-percent"),
        ("light_sensor_level", "Light Sensor Level", [l.name for l in LightSensorLevel], "mdi:brightness-5"),
    ]
    for key, name, opts, icon in select_defs:
        p = {
            "name": name,
            "unique_id": f"ambientika_{serial}_{key}_select",
            "state_topic": state,
            "value_template": f"{{{{ value_json.{key} }}}}",
            "command_topic": cmd_topic(prefix, serial, key),
            "options": opts,
            "availability_topic": avail,
            "device": device_info,
            "icon": icon,
        }
        entities.append((f"{base}/select/{serial}_{key}/config", p))

    return entities


# ---------------------------------------------------------------------------
# Bridge
# ---------------------------------------------------------------------------

class AmbientikaBridge:
    def __init__(self, cfg: BridgeConfig) -> None:
        self.cfg = cfg
        self.client: Optional[mqtt.Client] = None
        self.api: Optional[Ambientika] = None
        self.devices: dict = {}
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self._stop_event: Optional[asyncio.Event] = None

    # ----- MQTT -----
    def _mqtt_connect(self) -> None:
        self.client = mqtt.Client(client_id=self.cfg.mqtt_client_id, clean_session=True)
        if self.cfg.mqtt_user:
            self.client.username_pw_set(self.cfg.mqtt_user, self.cfg.mqtt_pass)
        if self.cfg.mqtt_tls:
            self.client.tls_set()
        self.client.on_connect = self._on_mqtt_connect
        self.client.on_message = self._on_mqtt_message
        log.info("Connecting to MQTT broker %s:%s ...", self.cfg.mqtt_host, self.cfg.mqtt_port)
        self.client.connect(self.cfg.mqtt_host, self.cfg.mqtt_port, keepalive=60)
        self.client.loop_start()

    def _on_mqtt_connect(self, client, userdata, flags, rc) -> None:
        if rc == 0:
            log.info("Connected to MQTT broker.")
            for serial in self.devices:
                topic = f"{self.cfg.topic_prefix}/{serial}/set/+"
                client.subscribe(topic)
                log.debug("Subscribed to %s", topic)
        else:
            log.error("MQTT connection failed (rc=%s).", rc)

    def _on_mqtt_message(self, client, userdata, msg) -> None:
        try:
            parts = msg.topic.split("/")
            if len(parts) < 4 or parts[-2] != "set":
                return
            serial = parts[-3]
            attr = parts[-1]
            payload = msg.payload.decode("utf-8", errors="replace").strip()
            log.info("Command received: serial=%s attr=%s value=%s", serial, attr, payload)
            if self.loop is not None:
                asyncio.run_coroutine_threadsafe(
                    self._handle_command(serial, attr, payload), self.loop
                )
        except Exception as e:
            log.exception("Error handling MQTT message: %s", e)

    async def _handle_command(self, serial: str, attr: str, value: str) -> None:
        device = self.devices.get(serial)
        if device is None:
            log.warning("Unknown device serial: %s", serial)
            return

        status_res = await device.status()
        if isinstance(status_res, Failure):
            log.error("Cannot read current status of %s: %s", serial, status_res)
            return
        status = status_res.unwrap()

        op = status["operating_mode"]
        fan = status["fan_speed"]
        hum = status["humidity_level"]
        light = status["light_sensor_level"]

        try:
            if attr == "operating_mode":
                op = OperatingMode[value]
            elif attr == "fan_speed":
                fan = FanSpeed[value]
            elif attr == "humidity_level":
                hum = HumidityLevel[value]
            elif attr == "light_sensor_level":
                light = LightSensorLevel[value]
            else:
                log.warning("Unsupported attribute: %s", attr)
                return
        except KeyError:
            log.error("Invalid value %r for %s", value, attr)
            return

        mode = {
            "operating_mode": op,
            "fan_speed": fan,
            "humidity_level": hum,
            "light_sensor_level": light,
        }
        res = await device.change_mode(mode)
        if isinstance(res, Failure):
            log.error("change_mode failed for %s: %s", serial, res)
        else:
            log.info("change_mode OK for %s", serial)

    # ----- Ambientika -----
    async def _login(self) -> None:
        log.info("Authenticating with Ambientika API at %s ...", self.cfg.host)
        res = await authenticate(self.cfg.username, self.cfg.password, self.cfg.host)
        if isinstance(res, Failure):
            log.error("Authentication failed: %s", res)
            raise RuntimeError("Cannot authenticate with Ambientika API. Check username/password.")
        self.api = res.unwrap()
        log.info("Authentication successful.")

    async def _discover_devices(self) -> None:
        assert self.api is not None
        houses_res = await self.api.houses()
        if isinstance(houses_res, Failure):
            log.error("Could not fetch houses: %s", houses_res)
            raise RuntimeError("Could not fetch houses from Ambientika API.")
        houses = houses_res.unwrap()

        self.devices = {}
        for house in houses:
            for room in house.rooms:
                for device in room.devices:
                    self.devices[device.serial_number] = device
                    log.info("  Device: %s (serial: %s)", device.name, device.serial_number)

        log.info("Found %d device(s).", len(self.devices))

    def _publish_discovery(self) -> None:
        if not self.cfg.enable_discovery or self.client is None:
            return
        for serial, device in self.devices.items():
            for topic, payload in build_discovery_configs(self.cfg, serial, device.name):
                self.client.publish(topic, json.dumps(payload), qos=0, retain=True)
        log.info("HA Auto-Discovery published for all devices.")

    async def _poll_loop(self) -> None:
        assert self._stop_event is not None
        while not self._stop_event.is_set():
            for serial, device in list(self.devices.items()):
                try:
                    res = await device.status()
                    if isinstance(res, Failure):
                        log.warning("status() failed for %s: %s", serial, res)
                        if self.client is not None:
                            self.client.publish(
                                avail_topic(self.cfg.topic_prefix, serial),
                                "offline",
                                qos=0,
                                retain=True,
                            )
                        continue
                    s = res.unwrap()
                    payload = {
                        "operating_mode": s["operating_mode"].name,
                        "fan_speed": s["fan_speed"].name,
                        "humidity_level": s["humidity_level"].name,
                        "light_sensor_level": s["light_sensor_level"].name,
                        "temperature": s["temperature"],
                        "humidity": s["humidity"],
                        "air_quality": s["air_quality"],
                        "humidity_alarm": s["humidity_alarm"],
                        "filters_status": s["filters_status"],
                        "night_alarm": s["night_alarm"],
                        "device_role": s["device_role"],
                    }
                    if self.client is not None:
                        self.client.publish(
                            state_topic(self.cfg.topic_prefix, serial),
                            json.dumps(payload),
                            qos=0,
                            retain=True,
                        )
                        self.client.publish(
                            avail_topic(self.cfg.topic_prefix, serial),
                            "online",
                            qos=0,
                            retain=True,
                        )
                except Exception as e:
                    log.exception("Error polling %s: %s", serial, e)

            try:
                await asyncio.wait_for(
                    self._stop_event.wait(), timeout=self.cfg.poll_interval
                )
            except asyncio.TimeoutError:
                pass

    async def run(self) -> None:
        self.loop = asyncio.get_running_loop()
        self._stop_event = asyncio.Event()

        await self._login()
        await self._discover_devices()
        self._mqtt_connect()
        if self.client is not None:
            for serial in self.devices:
                self.client.subscribe(f"{self.cfg.topic_prefix}/{serial}/set/+")
        self._publish_discovery()

        log.info("Starting poll loop (every %ss) ...", self.cfg.poll_interval)
        await self._poll_loop()

    def stop(self) -> None:
        log.info("Shutting down ...")
        if self._stop_event is not None and self.loop is not None:
            self.loop.call_soon_threadsafe(self._stop_event.set)
        if self.client is not None:
            try:
                self.client.loop_stop()
                self.client.disconnect()
            except Exception:
                pass


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def load_config() -> BridgeConfig:
    """Load configuration from Home Assistant options, YAML or environment."""
    ha_options = "/data/options.json"
    yaml_path = os.environ.get("CONFIG_YAML", "config.yaml")
    if os.path.exists(ha_options):
        return BridgeConfig.from_ha_options(ha_options)
    if os.path.exists(yaml_path):
        return BridgeConfig.from_yaml(yaml_path)
    return BridgeConfig.from_env()


def main() -> None:
    cfg = load_config()

    logging.basicConfig(
        level=getattr(logging, str(cfg.log_level).upper(), logging.INFO),
        format="%(asctime)s %(levelname)-7s %(message)s",
    )
    log.info("=== Ambientika MQTT Bridge v1.2.0 starting ===")
    log.info("API host      : %s", cfg.host)
    log.info("MQTT broker   : %s:%s", cfg.mqtt_host, cfg.mqtt_port)
    log.info("Topic prefix  : %s", cfg.topic_prefix)
    log.info("Poll interval : %ss", cfg.poll_interval)

    if not cfg.username or not cfg.password:
        log.error("Ambientika username/password missing. Set them in the add-on options or config.yaml.")
        sys.exit(1)

    bridge = AmbientikaBridge(cfg)

    def _handle_signal(*_):
        bridge.stop()

    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)

    try:
        asyncio.run(bridge.run())
    except KeyboardInterrupt:
        bridge.stop()
    except Exception as e:
        log.exception("Fatal error: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
