import json
import logging
from threading import Lock

import paho.mqtt.client as mqtt
from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import Batch, BatchInventory, InventoryEvent, Shelf


logger = logging.getLogger("smartshelf.mqtt")

MQTT_BROKER = "mosquitto"
MQTT_PORT = 1883
MQTT_TOPIC = "smartshelf/shelves/+/telemetry"

mqtt_client = None
mqtt_lock = Lock()


def process_telemetry(topic: str, payload: dict):
    """
    Process stock-change telemetry from a simulated smart shelf.
    """

    db = SessionLocal()

    try:
        # Extract shelf code from MQTT topic.
        topic_parts = topic.split("/")

        if len(topic_parts) != 4:
            logger.warning("Invalid MQTT topic: %s", topic)
            return

        shelf_code = topic_parts[2]

        # Validate payload.
        product_id = payload.get("product_id")
        batch_id = payload.get("batch_id")
        quantity_change = payload.get("quantity_change")

        if not all(
            isinstance(value, int)
            for value in (product_id, batch_id, quantity_change)
        ):
            logger.warning("Invalid telemetry payload: %s", payload)
            return

        if quantity_change == 0:
            logger.warning("Ignoring zero quantity change.")
            return

        # Identify shelf.
        shelf = db.scalar(
            select(Shelf).where(
                Shelf.code == shelf_code,
                Shelf.is_active.is_(True),
            )
        )

        if shelf is None:
            logger.warning("Unknown or inactive shelf: %s", shelf_code)
            return

        # Validate batch and product relationship.
        batch = db.get(Batch, batch_id)

        if batch is None or batch.product_id != product_id:
            logger.warning(
                "Invalid batch/product combination: %s / %s",
                batch_id,
                product_id,
            )
            return

        # Find existing inventory record.
        inventory = db.scalar(
            select(BatchInventory)
            .where(
                BatchInventory.batch_id == batch_id,
                BatchInventory.shelf_id == shelf.id,
            )
            .with_for_update()
        )

        if inventory is None:
            if quantity_change < 0:
                logger.warning(
                    "Cannot remove stock from an empty inventory record."
                )
                return

            inventory = BatchInventory(
                batch_id=batch_id,
                shelf_id=shelf.id,
                quantity=quantity_change,
            )

            db.add(inventory)
            db.flush()

            quantity_after = inventory.quantity

        else:
            new_quantity = inventory.quantity + quantity_change

            if new_quantity < 0:
                logger.warning(
                    "Rejected stock change. Current: %s, Change: %s",
                    inventory.quantity,
                    quantity_change,
                )
                return

            inventory.quantity = new_quantity
            quantity_after = new_quantity

        # Record inventory event.
        event = InventoryEvent(
            product_id=product_id,
            batch_id=batch_id,
            shelf_id=shelf.id,
            event_type="SIMULATED",
            quantity_change=quantity_change,
            quantity_after=quantity_after,
            source="SIMULATOR",
        )

        db.add(event)
        db.commit()

        logger.info(
            "MQTT inventory update successful | "
            "Shelf=%s | Product=%s | Batch=%s | Change=%s | New quantity=%s",
            shelf_code,
            product_id,
            batch_id,
            quantity_change,
            quantity_after,
        )

    except Exception:
        db.rollback()
        logger.exception("Failed to process MQTT telemetry.")

    finally:
        db.close()


def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        logger.info("Connected to MQTT broker.")

        client.subscribe(MQTT_TOPIC)

        logger.info("Subscribed to: %s", MQTT_TOPIC)

    else:
        logger.error(
            "MQTT connection failed. Reason code: %s",
            reason_code,
        )


def on_message(client, userdata, message):
    try:
        payload = json.loads(message.payload.decode("utf-8"))

        logger.info(
            "MQTT message received | Topic=%s | Payload=%s",
            message.topic,
            payload,
        )

        process_telemetry(message.topic, payload)

    except json.JSONDecodeError:
        logger.error("Invalid JSON received from MQTT.")

    except Exception:
        logger.exception("Unexpected error processing MQTT message.")


def start_mqtt():
    global mqtt_client

    with mqtt_lock:
        if mqtt_client is not None:
            return

        client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,
            client_id="smartshelf-backend",
        )

        client.on_connect = on_connect
        client.on_message = on_message

        try:
            client.connect(
                MQTT_BROKER,
                MQTT_PORT,
                keepalive=60,
            )

            client.loop_start()

            mqtt_client = client

            logger.info("MQTT service started.")

        except Exception:
            logger.exception("Could not start MQTT service.")


def stop_mqtt():
    global mqtt_client

    with mqtt_lock:
        if mqtt_client is not None:
            mqtt_client.loop_stop()
            mqtt_client.disconnect()

            mqtt_client = None

            logger.info("MQTT service stopped.")