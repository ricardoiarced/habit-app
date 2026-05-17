from datetime import date, timedelta
from app.models.entry import Entry
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

        # Current streak
        current_s = 0
        day = date.today()
        if day not in completed:
            day -= timedelta(days=1)
        while day in completed:
            current_s += 1
            day -= timedelta(days=1)

        # Max streak
        max_s = 0
        if completed:
            sorted_dates = sorted(completed)
            max_s = 1
            current_run = 1
            for i in range(1, len(sorted_dates)):
                if (sorted_dates[i] - sorted_dates[i - 1]).days == 1:
                    current_run += 1
                    max_s = max(max_s, current_run)
                else:
                    current_run = 1

        # % completion
        total_days = (date.today() - created_at).days + 1
        rate = round(len(completed) / total_days * 100, 1) if total_days > 0 and completed else 0.0

        return {
            "current_streak":  current_s,
            "max_streak":      max_s,
            "completion_rate": rate,
        }
