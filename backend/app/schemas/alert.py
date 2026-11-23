
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AlertOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int | None
    batch_id: int | None
    shelf_id: int | None
    alert_type: str
    priority: str
    title: str
    message: str
    is_read: bool
    is_resolved: bool
    created_at: datetime
    resolved_at: datetime | None
