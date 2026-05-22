from datetime import date
from app.repositories.habit_repository import HabitRepository
from app.repositories.entry_repository import EntryRepository
from app.services.streak_calculator import StreakCalculator
from app.models.habit import Habit
from sqlalchemy.orm import Session
import uuid

class HabitService:
    def __init__(self, session: Session):
        self.repo = HabitRepository(session)
        self.entry_repo = EntryRepository(session)
        self.streak_calc = StreakCalculator(session)
    
    def get_habits(self) -> list[Habit]:
        return self.repo.get_all()
    
    def add_habit(self, name: str) -> Habit:
        if not name.strip():
            raise ValueError("The Habit's name could not be empty!")
        return self.repo.create(name.strip())
    
    def delete_habit(self, habit_id) -> None:
        self.repo.delete(habit_id)
    
    def toggle_today(self, habit_id: uuid.UUID) -> bool:
        """Mark or unmark the habit today."""
        return self.entry_repo.toggle(habit_id, date.today())
    
    def is_completed_today(self, habit_id: uuid.UUID) -> bool:
        return self.entry_repo.is_completed_today(habit_id, date.today())
    
    def get_stats(self, habit: Habit) -> dict:
        """Return Current Streak, Max Streak, and Completion Rate."""
        return (self.streak_calc.get_all_stats(
            habit.id,
            habit.created_at.date()
        ))
