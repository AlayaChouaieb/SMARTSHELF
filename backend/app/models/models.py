from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Identity,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(
        BigInteger, Identity(), primary_key=True
    )
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[object] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class Supplier(Base):
    __tablename__ = "suppliers"

    id: Mapped[int] = mapped_column(
        BigInteger, Identity(), primary_key=True
    )
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    contact_name: Mapped[str | None] = mapped_column(String(160))
    email: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(40))
    address: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[object] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class Shelf(Base):
    __tablename__ = "shelves"

    id: Mapped[int] = mapped_column(
        BigInteger, Identity(), primary_key=True
    )
    code: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    location: Mapped[str | None] = mapped_column(String(160))
    description: Mapped[str | None] = mapped_column(Text)
    device_id: Mapped[str | None] = mapped_column(String(100), unique=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true"
    )
    created_at: Mapped[object] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class Product(Base):
    __tablename__ = "products"

    __table_args__ = (
        CheckConstraint("selling_price >= 0"),
        CheckConstraint("purchase_price >= 0"),
        CheckConstraint("min_stock >= 0"),
        CheckConstraint("max_stock IS NULL OR max_stock >= min_stock"),
    )

    id: Mapped[int] = mapped_column(
        BigInteger, Identity(), primary_key=True
    )
    barcode: Mapped[str | None] = mapped_column(String(100), unique=True)
    sku: Mapped[str | None] = mapped_column(String(80), unique=True)
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    brand: Mapped[str | None] = mapped_column(String(120))
    description: Mapped[str | None] = mapped_column(Text)
    category_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("categories.id", ondelete="SET NULL")
    )
    supplier_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("suppliers.id", ondelete="SET NULL")
    )
    unit: Mapped[str] = mapped_column(
        String(30), nullable=False, server_default="piece"
    )
    selling_price: Mapped[object] = mapped_column(
        Numeric(12, 3), nullable=False, server_default="0"
    )
    purchase_price: Mapped[object] = mapped_column(
        Numeric(12, 3), nullable=False, server_default="0"
    )
    min_stock: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )
    max_stock: Mapped[int | None] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true"
    )
    created_at: Mapped[object] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[object] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class Batch(Base):
    __tablename__ = "batches"

    __table_args__ = (
        UniqueConstraint("product_id", "batch_number"),
        CheckConstraint("received_quantity > 0"),
        CheckConstraint("purchase_price IS NULL OR purchase_price >= 0"),
    )

    id: Mapped[int] = mapped_column(
        BigInteger, Identity(), primary_key=True
    )
    product_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=False,
    )
    batch_number: Mapped[str] = mapped_column(String(100), nullable=False)
    expiration_date: Mapped[object] = mapped_column(Date, nullable=False)
    received_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    received_at: Mapped[object] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    purchase_price: Mapped[object | None] = mapped_column(Numeric(12, 3))
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[object] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class BatchInventory(Base):
    __tablename__ = "batch_inventory"

    __table_args__ = (
        UniqueConstraint("batch_id", "shelf_id"),
        CheckConstraint("quantity >= 0"),
    )

    id: Mapped[int] = mapped_column(
        BigInteger, Identity(), primary_key=True
    )
    batch_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("batches.id", ondelete="RESTRICT"),
        nullable=False,
    )
    shelf_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("shelves.id", ondelete="RESTRICT"),
        nullable=False,
    )
    quantity: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )
    updated_at: Mapped[object] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class InventoryEvent(Base):
    __tablename__ = "inventory_events"

    __table_args__ = (
        CheckConstraint(
            "event_type IN ('RESTOCK', 'SALE', 'REMOVAL', "
            "'ADJUSTMENT', 'EXPIRED', 'TRANSFER_IN', "
            "'TRANSFER_OUT', 'SIMULATED')"
        ),
        CheckConstraint("quantity_change <> 0"),
        CheckConstraint("quantity_after IS NULL OR quantity_after >= 0"),
        CheckConstraint(
            "source IN ('MANUAL', 'BARCODE', 'MQTT', 'SIMULATOR', 'SYSTEM')"
        ),
    )

    id: Mapped[int] = mapped_column(
        BigInteger, Identity(), primary_key=True
    )
    product_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=False,
    )
    batch_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("batches.id", ondelete="RESTRICT")
    )
    shelf_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("shelves.id", ondelete="SET NULL")
    )
    event_type: Mapped[str] = mapped_column(String(30), nullable=False)
    quantity_change: Mapped[int] = mapped_column(Integer, nullable=False)
    quantity_after: Mapped[int | None] = mapped_column(Integer)
    source: Mapped[str] = mapped_column(
        String(30), nullable=False, server_default="MANUAL"
    )
    reference_id: Mapped[str | None] = mapped_column(String(120))
    notes: Mapped[str | None] = mapped_column(Text)
    occurred_at: Mapped[object] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class Alert(Base):
    __tablename__ = "alerts"

    __table_args__ = (
        CheckConstraint(
            "alert_type IN ('LOW_STOCK', 'OUT_OF_STOCK', "
            "'EXPIRING_SOON', 'EXPIRED', 'ABNORMAL_STOCK_CHANGE')"
        ),
        CheckConstraint("priority IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')"),
    )

    id: Mapped[int] = mapped_column(
        BigInteger, Identity(), primary_key=True
    )
    product_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("products.id", ondelete="CASCADE")
    )
    batch_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("batches.id", ondelete="CASCADE")
    )
    shelf_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("shelves.id", ondelete="SET NULL")
    )
    alert_type: Mapped[str] = mapped_column(String(40), nullable=False)
    priority: Mapped[str] = mapped_column(
        String(15), nullable=False, server_default="MEDIUM"
    )
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false"
    )
    is_resolved: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false"
    )
    created_at: Mapped[object] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    resolved_at: Mapped[object | None] = mapped_column(
        DateTime(timezone=True)
    )