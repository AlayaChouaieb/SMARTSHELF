
import logging
import time

from config import PUBLISH_INTERVAL
from mqtt_publisher import MQTTPublisher
from shelf_simulator import ShelfSimulator


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

# Real records retrieved from the SMARTSHELF PostgreSQL database.
SHELVES = [
    {
        "code": "SHELF-A01",
        "products": [
            {
                "product_id": 1,
                "batch_id": 1,
            }
        ],
    }
]


def main():
    publisher = MQTTPublisher()
    simulator = ShelfSimulator(publisher, SHELVES)

    try:
        publisher.connect()
        logging.info("SMARTSHELF simulator started.")

        # Allow time for the MQTT connection callback.
        time.sleep(2)

        while True:
            simulator.simulate_stock_movement()
            time.sleep(PUBLISH_INTERVAL)

    except KeyboardInterrupt:
        logging.info("Stopping SMARTSHELF simulator.")

    finally:
        publisher.disconnect()


if __name__ == "__main__":
    main()
