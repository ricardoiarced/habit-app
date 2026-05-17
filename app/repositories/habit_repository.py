from sqlalchemy.orm import Session
from app.models import Habit

class HabitRepository:
    def __init__(self, session: Session):
        self.session = session
    
    def get_all(self) -> list[Habit]:
        return self.session.query(Habit).filter(Habit.is_active == True).all()
    
    def create(self, name: str, color: str = "#4A90D9") -> Habit:
        habit = Habit(name=name, color=color)
        self.session.add(habit)
        self.session.commit()
        self.session.refresh(habit)
        return habit
    
    def delete(self, habit_id) -> None:
        habit = self.session.get(Habit, habit_id)
        if habit:
            self.session.delete(habit)
            self.session.commit()