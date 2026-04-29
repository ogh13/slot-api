from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

class BookingCreate(BaseModel):
    resource_id: str
    slot_id: str
    client_name: str
    client_phone: str

class BookingResponse(BaseModel):
    id: str
    resource_id: str
    slot_id: str
    client_name: str
    client_phone: str
    status: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class BookingFilter(BaseModel):
    resource_id: Optional[str] = None
    date: Optional[datetime] = None
    status: Optional[str] = None
    client_name: Optional[str] = None
    client_phone: Optional[str] = None
    