import logging
import random

from mqtt_publisher import MQTTPublisher


logger = logging.getLogger("smartshelf.shelf")


class ShelfSimulator:

    def __init__(self, publisher: MQTTPublisher, shelves: list):
        self.publisher = publisher
        self.shelves = shelves

    def simulate_stock_movement(self):
        shelf = random.choice(self.shelves)
        product = random.choice(shelf["products"])

        # Negative = customer removes stock.
        # Positive = shelf is restocked.
        quantity_change = random.choice([-1, -1, -1, -2, 1, 2])

        success = self.publisher.publish_stock_change(
            shelf_code=shelf["code"],
            product_id=product["product_id"],
            batch_id=product["batch_id"],
            quantity_change=quantity_change,
        )

        if success:
            action = (
                "Customer purchase"
                if quantity_change < 0
                else "Restocking"
            )

            logger.info(
                "%s | Shelf=%s | Product=%s | Change=%s",
                action,
                shelf["code"],
                product["product_id"],
                quantity_change,
            )