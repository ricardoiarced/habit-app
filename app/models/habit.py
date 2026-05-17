import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, Text, ForeignKey, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class Habit(Base):
    __tablename__ = "habits"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str] = mapped_column(String(150), nullable=True)
    frequency: Mapped[str] = mapped_column(String(20), default="daily")
    color: Mapped[str] = mapped_column(String(7), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )
    
    user = relationship("User", back_populates="habits")
    entries = relationship("Entry", back_populates="habit", cascade="all, delete")
    reminders = relationship("Reminder", back_populates="habit", cascade="all, delete")