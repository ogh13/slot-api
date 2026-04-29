from pydantic import BaseModel, ConfigDict
from datetime import datetime

class ResourceCreate(BaseModel):
    name: str
    type: str

class ResourceResponse(BaseModel):
    id: str
    name: str
    type: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)