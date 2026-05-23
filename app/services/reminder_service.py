from datetime import time
from typing import Protocol
import uuid


class ReminderRepository(Protocol):
    def list_by_habit(self, habit_id: uuid.UUID): ...

    def has_active_reminders(self) -> bool: ...

    def get(self, reminder_id: uuid.UUID): ...

    def create(self, habit_id: uuid.UUID, reminder_time: time, days: list[int] | None): ...

    def update(
        self,
        reminder_id: uuid.UUID,
        reminder_time: time,
        days: list[int] | None,
    ): ...

    def delete(self, reminder_id: uuid.UUID) -> None: ...


class ReminderChangeNotifier(Protocol):
    def notify(self) -> None: ...


class ReminderService:
    def __init__(
        self,
        repository: ReminderRepository,
        change_notifier: ReminderChangeNotifier | None = None,
    ):
        self.repository = repository
        self.change_notifier = change_notifier

    def list_reminders(self, habit_id: uuid.UUID):
        return sorted(
            self.repository.list_by_habit(habit_id),
            key=lambda reminder: (reminder.reminder_time, reminder.days or []),
        )

    def has_active_reminders(self) -> bool:
        return self.repository.has_active_reminders()

    def create_reminder(
        self,
        habit_id: uuid.UUID,
        reminder_time: time,
        days: list[int] | None = None,
    ):
        normalized_time = self._normalize_time(reminder_time)
        normalized_days = self._normalize_days(days)
        self._ensure_no_overlap(habit_id, normalized_time, normalized_days)
        reminder = self.repository.create(
            habit_id,
            normalized_time,
            normalized_days,
        )
        self._notify_changed()
        return reminder

    def update_reminder(
        self,
        reminder_id: uuid.UUID,
        reminder_time: time,
        days: list[int] | None = None,
    ):
        reminder = self.repository.get(reminder_id)
        normalized_time = self._normalize_time(reminder_time)
        normalized_days = self._normalize_days(days)
        self._ensure_no_overlap(
            reminder.habit_id,
            normalized_time,
            normalized_days,
            exclude_reminder_id=reminder_id,
        )
        reminder = self.repository.update(reminder_id, normalized_time, normalized_days)
        self._notify_changed()
        return reminder

    def delete_reminder(self, reminder_id: uuid.UUID) -> None:
        self.repository.delete(reminder_id)
        self._notify_changed()

    def _normalize_time(self, reminder_time: time) -> time:
        return reminder_time.replace(second=0, microsecond=0)

    def _normalize_days(self, days: list[int] | None) -> list[int] | None:
        if days is None:
            return None
        if not days:
            raise ValueError("select at least one weekday")
        if any(day < 0 or day > 6 for day in days):
            raise ValueError("weekday must be between 0 and 6")
        normalized_days = sorted(set(days))
        return None if normalized_days == list(range(7)) else normalized_days

    def _ensure_no_overlap(
        self,
        habit_id: uuid.UUID,
        reminder_time: time,
        days: list[int] | None,
        exclude_reminder_id: uuid.UUID | None = None,
    ) -> None:
        new_days = self._day_scope(days)
        for reminder in self.repository.list_by_habit(habit_id):
            if reminder.id == exclude_reminder_id:
                continue
            if reminder.reminder_time != reminder_time:
                continue
            if new_days & self._day_scope(reminder.days):
                raise ValueError("Reminder overlaps an existing Reminder")

    def _day_scope(self, days: list[int] | None) -> set[int]:
        return set(range(7)) if days is None else set(days)

    def _notify_changed(self) -> None:
        if self.change_notifier:
            self.change_notifier.notify()
