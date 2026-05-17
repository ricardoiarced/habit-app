from app.repositories.habit_repository import HabitRepository
from app.models.habit import Habit
from sqlalchemy.orm import Session

class HabitService:
    def __init__(self, session: Session):
        self.repo = HabitRepository(session)
    
    def get_habits(self) -> list[Habit]:
        return self.repo.get_all()
    
    def add_habit(self, name: str) -> Habit:
        if not name.strip():
            raise ValueError("The Habit's name could not be empty!")
        return self.repo.create(name.strip())
    
    def delete_habit(self, habit_id) -> None:
        self.repo.delete(habit_id)