
from datetime import datetime, timezone

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.models import Alert


MONITORED_TYPES = (
    "LOW_STOCK",
    "OUT_OF_STOCK",
    "EXPIRING_SOON",
    "EXPIRED",
)


def refresh_alerts(db: Session):
    active_conditions = {}

    # Detect products with low or zero stock.
    stock_rows = db.execute(
        text("""
            SELECT
                product_id,
                product_name,
                total_quantity,
                min_stock,
                stock_status
            FROM product_stock
            WHERE stock_status IN ('LOW_STOCK', 'OUT_OF_STOCK')
        """)
    ).mappings().all()

    for row in stock_rows:
        alert_type = row["stock_status"]
        product_id = row["product_id"]

        key = (alert_type, product_id, None, None)

        if alert_type == "OUT_OF_STOCK":
            priority = "HIGH"
            title = f"Out of stock: {row['product_name']}"
            message = f"{row['product_name']} has no remaining stock."
        else:
            priority = "MEDIUM"
            title = f"Low stock: {row['product_name']}"
            message = (
                f"{row['product_name']} has {row['total_quantity']} "
                f"units remaining. Minimum stock is {row['min_stock']}."
            )

        active_conditions[key] = {
            "product_id": product_id,
            "batch_id": None,
            "shelf_id": None,
            "priority": priority,
            "title": title,
            "message": message,
        }

    # Detect batches that are expiring or already expired.
    expiry_rows = db.execute(
        text("""
            SELECT
                batch_id,
                product_id,
                product_name,
                batch_number,
                expiration_date,
                remaining_quantity,
                days_remaining,
                expiry_status
            FROM batch_expiry_status
            WHERE expiry_status IN (
                'EXPIRING_SOON',
                'EXPIRED',
                'EXPIRES_TODAY'
            )
            AND remaining_quantity > 0
        """)
    ).mappings().all()

    for row in expiry_rows:
        expiry_status = row["expiry_status"]

        if expiry_status == "EXPIRES_TODAY":
            alert_type = "EXPIRING_SOON"
            priority = "HIGH"
            description = "expires today"

        elif expiry_status == "EXPIRED":
            alert_type = "EXPIRED"
            priority = "CRITICAL"
            description = "has expired"

        else:
            alert_type = "EXPIRING_SOON"
            priority = (
                "HIGH" if row["days_remaining"] <= 3 else "MEDIUM"
            )
            description = f"expires in {row['days_remaining']} days"

        key = (
            alert_type,
            row["product_id"],
            row["batch_id"],
            None,
        )

        active_conditions[key] = {
            "product_id": row["product_id"],
            "batch_id": row["batch_id"],
            "shelf_id": None,
            "priority": priority,
            "title": (
                f"{'Expired' if alert_type == 'EXPIRED' else 'Expiring'}: "
                f"{row['product_name']}"
            ),
            "message": (
                f"Batch {row['batch_number']} {description}. "
                f"Remaining quantity: {row['remaining_quantity']}. "
                f"Expiration date: {row['expiration_date']}."
            ),
        }

    # Load existing unresolved alerts.
    existing_alerts = db.scalars(
        select(Alert).where(
            Alert.is_resolved.is_(False),
            Alert.alert_type.in_(MONITORED_TYPES),
        )
    ).all()

    existing_by_key = {}

    for alert in existing_alerts:
        key = (
            alert.alert_type,
            alert.product_id,
            alert.batch_id,
            alert.shelf_id,
        )

        if key not in existing_by_key:
            existing_by_key[key] = alert
        else:
            # Resolve duplicate unresolved alerts.
            alert.is_resolved = True
            alert.resolved_at = datetime.now(timezone.utc)

    created = 0
    updated = 0
    resolved = 0

    # Create new alerts or update existing ones.
    for key, condition in active_conditions.items():
        alert_type = key[0]
        alert = existing_by_key.get(key)

        if alert is None:
            alert = Alert(
                alert_type=alert_type,
                priority=condition["priority"],
                title=condition["title"],
                message=condition["message"],
                product_id=condition["product_id"],
                batch_id=condition["batch_id"],
                shelf_id=condition["shelf_id"],
            )
            db.add(alert)
            created += 1

        else:
            alert.priority = condition["priority"]
            alert.title = condition["title"]
            alert.message = condition["message"]
            updated += 1

    # Resolve alerts when their conditions no longer exist.
    active_keys = set(active_conditions.keys())

    for key, alert in existing_by_key.items():
        if key not in active_keys:
            alert.is_resolved = True
            alert.resolved_at = datetime.now(timezone.utc)
            resolved += 1

    db.commit()

    return {
        "created": created,
        "updated": updated,
        "resolved": resolved,
        "active_conditions": len(active_conditions),
    }
