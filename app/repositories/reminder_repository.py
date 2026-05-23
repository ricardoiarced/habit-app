from datetime import time
import uuid

from sqlalchemy.orm import Session, joinedload

from app.models import Habit, Reminder


class ReminderRepository:
    def __init__(self, session: Session):
        self.session = session

    def list_by_habit(self, habit_id: uuid.UUID) -> list[Reminder]:
        return (
            self.session.query(Reminder)
            .filter(Reminder.habit_id == habit_id)
            .order_by(Reminder.reminder_time.asc(), Reminder.days.asc().nullsfirst())
            .all()
        )

    def list_active(self) -> list[Reminder]:
        return (
            self.session.query(Reminder)
            .join(Reminder.habit)
            .options(joinedload(Reminder.habit))
            .filter(Habit.is_active == True)
            .order_by(Reminder.reminder_time.asc(), Reminder.days.asc().nullsfirst())
            .all()
        )

    def has_active_reminders(self) -> bool:
        return (
            self.session.query(Reminder.id)
            .join(Reminder.habit)
            .filter(Habit.is_active == True)
            .first()
            is not None
        )

    def get(self, reminder_id: uuid.UUID) -> Reminder:
        reminder = self.session.get(Reminder, reminder_id)
        if reminder is None:
            raise ValueError("Reminder not found")
        return reminder

    def get_active(self, reminder_id: uuid.UUID) -> Reminder | None:
        return (
            self.session.query(Reminder)
            .join(Reminder.habit)
            .options(joinedload(Reminder.habit))
            .filter(Reminder.id == reminder_id, Habit.is_active == True)
            .first()
        )

    def create(
        self,
        habit_id: uuid.UUID,
        reminder_time: time,
        days: list[int] | None,
    ) -> Reminder:
        reminder = Reminder(
            habit_id=habit_id,
            reminder_time=reminder_time,
            days=days,
        )
        self.session.add(reminder)
        self.session.commit()
        self.session.refresh(reminder)
        return reminder

    def update(
        self,
        reminder_id: uuid.UUID,
        reminder_time: time,
        days: list[int] | None,
    ) -> Reminder:
        reminder = self.get(reminder_id)
        reminder.reminder_time = reminder_time
        reminder.days = days
        self.session.commit()
        self.session.refresh(reminder)
        return reminder

    def delete(self, reminder_id: uuid.UUID) -> None:
        reminder = self.get(reminder_id)
        self.session.delete(reminder)
        self.session.commit()
