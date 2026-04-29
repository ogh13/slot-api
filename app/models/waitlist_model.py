import enum
import uuid
from sqlalchemy import Column, String, ForeignKey, DateTime, Enum as SAEnum, func
from app.database import Base

class WaitlistStatus(str, enum.Enum):
    WAITING = "waiting"
    NOTIFIED = "notified"

class Waitlist(Base):
    __tablename__ = "waitlist"
    id = Column(String(255), primary_key=True, default=lambda: str(uuid.uuid4()))
    slot_id = Column(String(255), ForeignKey("slots.id", ondelete="CASCADE"), nullable=False)
    client_name = Column(String, nullable=False)
    client_phone = Column(String, nullable=False)
    status = Column(SAEnum(WaitlistStatus), default=WaitlistStatus.WAITING, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())