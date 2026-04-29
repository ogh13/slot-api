from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

class NotificationResponse(BaseModel):
    id: str
    booking_id: str
    trigger: str
    scheduled_for: datetime
    status: str
    created_at: datetime
    sent_at: Optional[datetime]
    model_config = ConfigDict(from_attributes=True)