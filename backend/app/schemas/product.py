from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ProductCreate(BaseModel):
    barcode: str | None = Field(default=None, max_length=100)
    sku: str | None = Field(default=None, max_length=80)
    name: str = Field(min_length=1, max_length=180)
    brand: str | None = Field(default=None, max_length=120)
    description: str | None = None
    category_id: int | None = None
    supplier_id: int | None = None
    unit: str = Field(default="piece", max_length=30)
    selling_price: Decimal = Field(default=Decimal("0"), ge=0)
    purchase_price: Decimal = Field(default=Decimal("0"), ge=0)
    min_stock: int = Field(default=0, ge=0)
    max_stock: int | None = Field(default=None, ge=0)
    is_active: bool = True


class ProductUpdate(BaseModel):
    barcode: str | None = Field(default=None, max_length=100)
    sku: str | None = Field(default=None, max_length=80)
    name: str | None = Field(default=None, min_length=1, max_length=180)
    brand: str | None = Field(default=None, max_length=120)
    description: str | None = None
    category_id: int | None = None
    supplier_id: int | None = None
    unit: str | None = Field(default=None, max_length=30)
    selling_price: Decimal | None = Field(default=None, ge=0)
    purchase_price: Decimal | None = Field(default=None, ge=0)
    min_stock: int | None = Field(default=None, ge=0)
    max_stock: int | None = Field(default=None, ge=0)
    is_active: bool | None = None


class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    barcode: str | None
    sku: str | None
    name: str
    brand: str | None
    description: str | None
    category_id: int | None
    supplier_id: int | None
    unit: str
    selling_price: Decimal
    purchase_price: Decimal
    min_stock: int
    max_stock: int | None
    is_active: bool
    created_at: datetime
    updated_at: datetime