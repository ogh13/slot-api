from pydantic import BaseModel, ConfigDict
from datetime import datetime

class WaitlistCreate(BaseModel):
    client_name: str
    client_phone: str

class WaitlistResponse(BaseModel):
    id: str
    slot_id: str
    client_name: str
    client_phone: str
    status: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class WaitlistListResponse(BaseModel):
    items: list[WaitlistResponse]