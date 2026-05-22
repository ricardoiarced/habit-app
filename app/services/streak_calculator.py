from datetime import date
from app.models.entry import Entry
from app.services.habit_stats import calculate_habit_stats
from sqlalchemy.orm import Session
import uuid

class StreakCalculator:
    def __init__(self, session: Session):
        self.session = session
    
    def _get_completed_dates(self, habit_id: uuid.UUID) -> set[date]:
        """Return the completed dates for a habit."""
        entries = (
            self.session.query(Entry.completed_at)
            .filter(Entry.habit_id == habit_id)
            .all()
        )
        return {entry.completed_at for entry in entries}
    
    def get_all_stats(self, habit_id: uuid.UUID, created_at: date) -> dict:
        """Calcula todas las estadísticas en una sola query."""
        completed = self._get_completed_dates(habit_id)
        return calculate_habit_stats(completed, created_at, date.today())
