
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_db

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/summary")
def dashboard_summary(db: Session = Depends(get_db)):
    total_products = db.execute(
        text("""
            SELECT COUNT(*)
            FROM products
            WHERE is_active = TRUE
        """)
    ).scalar_one()

    total_stock = db.execute(
        text("""
            SELECT COALESCE(SUM(total_quantity), 0)
            FROM product_stock
        """)
    ).scalar_one()

    stock_counts = db.execute(
        text("""
            SELECT
                COUNT(*) FILTER (
                    WHERE stock_status = 'LOW_STOCK'
                ) AS low_stock,
                COUNT(*) FILTER (
                    WHERE stock_status = 'OUT_OF_STOCK'
                ) AS out_of_stock
            FROM product_stock
        """)
    ).mappings().one()

    expiry_counts = db.execute(
        text("""
            SELECT
                COUNT(*) FILTER (
                    WHERE expiry_status = 'EXPIRING_SOON'
                      AND remaining_quantity > 0
                ) AS expiring_soon,
                COUNT(*) FILTER (
                    WHERE expiry_status = 'EXPIRES_TODAY'
                      AND remaining_quantity > 0
                ) AS expires_today,
                COUNT(*) FILTER (
                    WHERE expiry_status = 'EXPIRED'
                      AND remaining_quantity > 0
                ) AS expired
            FROM batch_expiry_status
        """)
    ).mappings().one()

    alert_counts = db.execute(
        text("""
            SELECT
                COUNT(*) FILTER (
                    WHERE is_resolved = FALSE
                ) AS active_alerts,
                COUNT(*) FILTER (
                    WHERE is_read = FALSE
                      AND is_resolved = FALSE
                ) AS unread_alerts
            FROM alerts
        """)
    ).mappings().one()

    return {
        "total_products": total_products,
        "total_stock_units": total_stock,
        "low_stock_products": stock_counts["low_stock"],
        "out_of_stock_products": stock_counts["out_of_stock"],
        "expiring_batches": expiry_counts["expiring_soon"],
        "batches_expiring_today": expiry_counts["expires_today"],
        "expired_batches": expiry_counts["expired"],
        "active_alerts": alert_counts["active_alerts"],
        "unread_alerts": alert_counts["unread_alerts"],
    }
