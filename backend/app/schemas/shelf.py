
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ShelfCreate(BaseModel):
    code: str = Field(min_length=1, max_length=40)
    name: str = Field(min_length=1, max_length=120)
    location: str | None = None
    description: str | None = None
    device_id: str | None = Field(default=None, max_length=100)


class ShelfUpdate(BaseModel):
    code: str | None = Field(default=None, min_length=1, max_length=40)
    name: str | None = Field(default=None, min_length=1, max_length=120)
    location: str | None = None
    description: str | None = None
    device_id: str | None = Field(default=None, max_length=100)


class ShelfOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    location: str | None
    description: str | None
    device_id: str | None
    is_active: bool
    created_at: datetime
