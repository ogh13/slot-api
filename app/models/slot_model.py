import uuid
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from app.database import Base

class Slot(Base):
    __tablename__ = "slots"
    id = Column(String(255), primary_key=True, default=lambda: str(uuid.uuid4()))
    resource_id = Column(String(255), ForeignKey("resources.id", ondelete="CASCADE"), nullable=False)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    is_booked = Column(Boolean, default=False, nullable=False)

    resource = relationship("Resource", backref="slots")