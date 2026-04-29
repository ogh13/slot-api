import enum
import uuid
from sqlalchemy import Column, String, ForeignKey, DateTime, Enum as SAEnum, func
from sqlalchemy.orm import relationship
from app.database import Base

class NotificationStatus(str, enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    CANCELLED = "cancelled"

class Notification(Base):
    __tablename__ = "notifications"
    id = Column(String(255), primary_key=True, default=lambda: str(uuid.uuid4()))
    booking_id = Column(String(255), ForeignKey("bookings.id", ondelete="CASCADE"), nullable=True)

    trigger = Column(String, nullable=False)          # "24h_before" / "1h_before"
    scheduled_for = Column(DateTime(timezone=True), nullable=False)
    status = Column(SAEnum(NotificationStatus), default=NotificationStatus.PENDING, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    sent_at = Column(DateTime(timezone=True), nullable=True)
    job_id = Column(String, nullable=True)            # ID du job ARQ correspondant

    booking = relationship("Booking", backref="notifications")