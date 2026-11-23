import json
import logging
from datetime import datetime, timezone

import paho.mqtt.client as mqtt

from config import MQTT_BROKER, MQTT_PORT, MQTT_TOPIC_TEMPLATE


logger = logging.getLogger("smartshelf.simulator")


class MQTTPublisher:

    def __init__(self):
        self.client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,
            client_id="smartshelf-simulator",
        )

        self.connected = False
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect

    def on_connect(self, client, userdata, flags, reason_code, properties):
        if reason_code == 0:
            self.connected = True
            logger.info("Connected to MQTT broker.")
        else:
            logger.error("MQTT connection failed: %s", reason_code)

    def on_disconnect(self, client, userdata, disconnect_flags, reason_code, properties):
        self.connected = False
        logger.warning("Disconnected from MQTT broker.")

    def connect(self):
        self.client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
        self.client.loop_start()

    def publish_stock_change(
        self,
        shelf_code: str,
        product_id: int,
        batch_id: int,
        quantity_change: int,
    ):
        topic = MQTT_TOPIC_TEMPLATE.format(shelf_code=shelf_code)

        payload = {
            "device_id": shelf_code,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": "STOCK_CHANGE",
            "product_id": product_id,
            "batch_id": batch_id,
            "quantity_change": quantity_change,
        }

        if not self.connected:
            logger.error("Cannot publish: MQTT client is disconnected.")
            return False

        result = self.client.publish(
            topic,
            json.dumps(payload),
            qos=1,
        )

        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            logger.info("Published: %s | %s", topic, payload)
            return True

        logger.error("Publish failed: %s", result.rc)
        return False

    def disconnect(self):
        self.client.loop_stop()
        self.client.disconnect()