import uuid
from datetime import time

import pytest

from app.services.reminder_service import ReminderService


class InMemoryReminderRepository:
    def __init__(self):
        self.reminders = []

    def list_by_habit(self, habit_id):
        return [reminder for reminder in self.reminders if reminder.habit_id == habit_id]

    def create(self, habit_id, reminder_time, days):
        reminder = type(
            "ReminderRecord",
            (),
            {
                "id": uuid.uuid4(),
                "habit_id": habit_id,
                "habit_name": "Read 30 minutes",
                "reminder_time": reminder_time,
                "days": days,
            },
        )()
        self.reminders.append(reminder)
        return reminder

    def get(self, reminder_id):
        return next(
            reminder for reminder in self.reminders if reminder.id == reminder_id
        )

    def update(self, reminder_id, reminder_time, days):
        reminder = self.get(reminder_id)
        reminder.reminder_time = reminder_time
        reminder.days = days
        return reminder

    def delete(self, reminder_id):
        self.reminders = [
            reminder for reminder in self.reminders if reminder.id != reminder_id
        ]


class CountingNotifier:
    def __init__(self):
        self.count = 0

    def notify(self):
        self.count += 1


def test_creating_every_day_reminder_normalizes_to_minute_precision():
    habit_id = uuid.uuid4()
    repository = InMemoryReminderRepository()
    service = ReminderService(repository)

    reminder = service.create_reminder(
        habit_id,
        time(8, 30, 45),
        days=None,
    )

    assert reminder.reminder_time == time(8, 30)
    assert reminder.days is None
    assert service.list_reminders(habit_id) == [reminder]


def test_creating_custom_weekday_reminder_normalizes_days():
    habit_id = uuid.uuid4()
    repository = InMemoryReminderRepository()
    service = ReminderService(repository)

    reminder = service.create_reminder(
        habit_id,
        time(8, 30),
        days=[2, 0, 2],
    )
    daily_reminder = service.create_reminder(
        habit_id,
        time(9, 0),
        days=[0, 1, 2, 3, 4, 5, 6],
    )

    assert reminder.days == [0, 2]
    assert daily_reminder.days is None


def test_creating_custom_weekday_reminder_rejects_invalid_days():
    service = ReminderService(InMemoryReminderRepository())

    with pytest.raises(ValueError, match="select at least one weekday"):
        service.create_reminder(uuid.uuid4(), time(8, 30), days=[])

    with pytest.raises(ValueError, match="weekday must be between 0 and 6"):
        service.create_reminder(uuid.uuid4(), time(8, 30), days=[0, 7])


def test_creating_reminder_rejects_overlapping_same_time_scope():
    habit_id = uuid.uuid4()
    service = ReminderService(InMemoryReminderRepository())

    service.create_reminder(habit_id, time(8, 0), days=[0, 2, 4])

    with pytest.raises(ValueError, match="overlaps an existing Reminder"):
        service.create_reminder(habit_id, time(8, 0), days=[2])


def test_updating_reminder_normalizes_and_rejects_overlaps():
    habit_id = uuid.uuid4()
    service = ReminderService(InMemoryReminderRepository())
    reminder = service.create_reminder(habit_id, time(8, 0), days=[0])
    service.create_reminder(habit_id, time(9, 0), days=[2])

    updated = service.update_reminder(reminder.id, time(9, 0, 30), days=[4, 4])

    assert updated.reminder_time == time(9, 0)
    assert updated.days == [4]
    with pytest.raises(ValueError, match="overlaps an existing Reminder"):
        service.update_reminder(reminder.id, time(9, 0), days=[2])


def test_deleting_reminder_removes_it_from_the_habit():
    habit_id = uuid.uuid4()
    service = ReminderService(InMemoryReminderRepository())
    reminder = service.create_reminder(habit_id, time(8, 0))

    service.delete_reminder(reminder.id)

    assert service.list_reminders(habit_id) == []


def test_reminder_changes_notify_the_worker_to_reconcile():
    notifier = CountingNotifier()
    service = ReminderService(InMemoryReminderRepository(), notifier)
    reminder = service.create_reminder(uuid.uuid4(), time(8, 0))

    service.update_reminder(reminder.id, time(9, 0))
    service.delete_reminder(reminder.id)

    assert notifier.count == 3
