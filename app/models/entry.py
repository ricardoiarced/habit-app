import uuid
from datetime import date, datetime
from sqlalchemy import Date, Text, ForeignKey, UniqueConstraint, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class Entry(Base):
    __tablename__ = "entries"
    
    __table_args__ = (UniqueConstraint("habit_id", "completed_at"),)
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4) 
    habit_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("habits.id", ondelete="CASCADE"))
    completed_at: Mapped[date] = mapped_column(Date, nullable=False)
    note: Mapped[str] = mapped_column(Text, nullable=True)
    
    habit = relationship("Habit", back_populates="entries")