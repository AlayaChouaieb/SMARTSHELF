
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class BatchCreate(BaseModel):
    product_id: int = Field(gt=0)
    batch_number: str = Field(min_length=1, max_length=100)
    expiration_date: date
    received_quantity: int = Field(gt=0)
    purchase_price: Decimal | None = Field(default=None, ge=0)
    notes: str | None = None


class BatchUpdate(BaseModel):
    batch_number: str | None = Field(
        default=None, min_length=1, max_length=100
    )
    expiration_date: date | None = None
    purchase_price: Decimal | None = Field(default=None, ge=0)
    notes: str | None = None


class BatchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    batch_number: str
    expiration_date: date
    received_quantity: int
    received_at: datetime
    purchase_price: Decimal | None
    notes: str | None
    created_at: datetime
