from pydantic import BaseModel, field_validator, ConfigDict
from datetime import datetime, timezone
from typing import List

class SlotCreate(BaseModel):
    start_time: datetime
    end_time: datetime

    @field_validator("end_time")
    @classmethod
    def end_after_start(cls, v, info):
        if "start_time" in info.data and v <= info.data["start_time"]:
            raise ValueError("end_time must be after start_time")
        return v

    @field_validator("start_time")
    @classmethod
    def start_not_past(cls, v):
        if v <= datetime.now(timezone.utc):
            raise ValueError("start_time cannot be in the past")
        return v

class AvailabilityCreate(BaseModel):
    slots: List[SlotCreate]

class SlotResponse(BaseModel):
    id: str
    resource_id: str
    start_time: datetime
    end_time: datetime
    is_booked: bool
    model_config = ConfigDict(from_attributes=True)