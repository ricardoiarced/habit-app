from datetime import date
from sqlalchemy.orm import Session
from app.models.entry import Entry
import uuid

class EntryRepository:
    def __init__(self, session: Session):
        self.session = session
    
    def get_by_habit(self, habit_id: uuid.UUID) -> list[Entry]:
        return (
            self.session.query(Entry)
            .filter(Entry.habit_id == habit_id)
            .order_by(Entry.completed_at.desc())
            .all()
        )
    
    def toggle(self, habit_id: uuid.UUID, day: date) -> bool:
        """Toggle or untoggle a day. Returns True if a day stayed marked."""
        existing = (
            self.session.query(Entry)
            .filter(Entry.habit_id == habit_id, Entry.completed_at == day)
            .first()
        )
        if existing:
            self.session.delete(existing)
            self.session.commit()
            self.session.expire_all()
            return False
        else:
            entry = Entry(habit_id=habit_id, completed_at=day)
            self.session.add(entry)
            self.session.commit()
            self.session.expire_all()
            return True
    
    def is_completed_today(self, habit_id: uuid.UUID, day: date) -> bool:
        return (
            self.session.query(Entry)
            .filter(Entry.habit_id == habit_id, 
                    Entry.completed_at == date.today()
                    )
            .first() is not None
        )