import uuid
from datetime import datetime, time
from sqlalchemy import Time, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ARRAY, INTEGER
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class Reminder(Base):
    __tablename__ = "reminders"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    habit_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("habits.id", ondelete="CASCADE"))
    reminder_time: Mapped[time] = mapped_column(Time, nullable=False)
    days: Mapped[list] = mapped_column(ARRAY(INTEGER), nullable=True)
    
    habit = relationship("Habit", back_populates="reminders")