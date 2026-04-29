import enum
from sqlalchemy import Column, String, ForeignKey, DateTime, Enum as SAEnum, func
from sqlalchemy.orm import relationship
from app.database import Base
import uuid

class BookingStatus(str, enum.Enum):
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"

class Booking(Base):
    __tablename__ = "bookings"
    id = Column(String(255), primary_key=True, default=lambda: str(uuid.uuid4()))
    resource_id = Column(String(255), ForeignKey("resources.id"), nullable=False)
    slot_id = Column(String(255), ForeignKey("slots.id"), nullable=False)
    client_name = Column(String, nullable=False)
    client_phone = Column(String, nullable=False)
    status = Column(SAEnum(BookingStatus), default=BookingStatus.CONFIRMED, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    resource = relationship("Resource", backref="bookings")
    slot = relationship("Slot", backref="bookings")