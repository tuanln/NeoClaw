"""MQTT client for device telemetry and commands."""
from __future__ import annotations

import json
import logging
from typing import Callable

from neoclaw.config.settings import get_settings
from neoclaw.iot.models import TelemetryPacket

logger = logging.getLogger(__name__)


class MQTTClient:
    """MQTT pub/sub client for NeoClaw device communication.

    Topics:
    - neoclaw/{device_id}/telemetry — device → cloud
    - neoclaw/{device_id}/command — cloud → device
    - neoclaw/{device_id}/status — device status updates
    """

    def __init__(self, device_id: str = "default"):
        self._settings = get_settings().iot
        self._device_id = device_id
        self._client = None
        self._connected = False
        self._callbacks: dict[str, list[Callable]] = {}

    @property
    def prefix(self) -> str:
        return f"{self._settings.mqtt_topic_prefix}/{self._device_id}"

    def connect(self) -> bool:
        """Connect to MQTT broker."""
        try:
            import paho.mqtt.client as mqtt

            self._client = mqtt.Client(
                callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
                client_id=f"neoclaw-{self._device_id}",
            )
            self._client.on_connect = self._on_connect
            self._client.on_message = self._on_message
            self._client.on_disconnect = self._on_disconnect
            self._client.connect(self._settings.mqtt_broker, self._settings.mqtt_port)
            self._client.loop_start()
            return True
        except ImportError:
            logger.warning("paho-mqtt not installed")
            return False
        except Exception as e:
            logger.error(f"MQTT connection failed: {e}")
            return False

    def disconnect(self) -> None:
        """Disconnect from MQTT broker."""
        if self._client:
            self._client.loop_stop()
            self._client.disconnect()
            self._connected = False

    def publish_telemetry(self, packet: TelemetryPacket) -> None:
        """Publish telemetry data."""
        self._publish(f"{self.prefix}/telemetry", packet.to_dict())

    def publish_status(self, status: str) -> None:
        """Publish device status."""
        self._publish(f"{self.prefix}/status", {"status": status})

    def subscribe_commands(self, callback: Callable[[dict], None]) -> None:
        """Subscribe to command topic."""
        topic = f"{self.prefix}/command"
        if topic not in self._callbacks:
            self._callbacks[topic] = []
        self._callbacks[topic].append(callback)
        if self._client and self._connected:
            self._client.subscribe(topic)

    def _publish(self, topic: str, data: dict) -> None:
        if self._client and self._connected:
            payload = json.dumps(data)
            self._client.publish(topic, payload)
            logger.debug(f"Published to {topic}: {len(payload)} bytes")

    def _on_connect(self, client, userdata, flags, reason_code, properties=None) -> None:
        self._connected = True
        logger.info("Connected to MQTT broker")
        for topic in self._callbacks:
            client.subscribe(topic)

    def _on_disconnect(self, client, userdata, flags, reason_code, properties=None) -> None:
        self._connected = False
        logger.warning("Disconnected from MQTT broker")

    def _on_message(self, client, userdata, msg) -> None:
        try:
            data = json.loads(msg.payload.decode())
            callbacks = self._callbacks.get(msg.topic, [])
            for callback in callbacks:
                callback(data)
        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON on {msg.topic}")

    @property
    def is_connected(self) -> bool:
        return self._connected
