
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class InventoryReceive(BaseModel):
    batch_id: int = Field(gt=0)
    shelf_id: int = Field(gt=0)
    quantity: int = Field(gt=0)
    notes: str | None = None


class InventoryAdjust(BaseModel):
    new_quantity: int = Field(ge=0)
    notes: str | None = None


class InventoryOut(BaseModel):
    id: int
    batch_id: int
    shelf_id: int
    product_id: int
    product_name: str
    batch_number: str
    shelf_code: str
    shelf_name: str
    quantity: int
    updated_at: datetime


class InventoryEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    batch_id: int | None
    shelf_id: int | None
    event_type: str
    quantity_change: int
    quantity_after: int | None
    source: str
    reference_id: str | None
    notes: str | None
    occurred_at: datetime
