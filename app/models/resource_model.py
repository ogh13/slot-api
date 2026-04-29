import uuid
from sqlalchemy import Column, String, DateTime, func
from app.database import Base

class Resource(Base):
    __tablename__ = "resources"
    id = Column(String(255), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())