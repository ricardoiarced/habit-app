import uuid
from datetime import date, time
from types import SimpleNamespace

from app.services.reminder_worker import ReminderJobRunner, ReminderJobScheduler


class FakeReminderRepository:
    def __init__(self, reminder):
        self.reminder = reminder

    def get_active(self, reminder_id):
        if self.reminder and self.reminder.id == reminder_id:
            return self.reminder
        return None


class FailingReminderRepository:
    def get_active(self, reminder_id):
        raise RuntimeError("database unavailable")


class ActiveReminderRepository(FakeReminderRepository):
    def list_active(self):
        return [self.reminder] if self.reminder else []


class FakeScheduler:
    def __init__(self):
        self.jobs = {}
        self.removed_job_ids = []

    def get_jobs(self):
        return [SimpleNamespace(id=job_id) for job_id in self.jobs]

    def add_job(self, func, trigger, **kwargs):
        self.jobs[kwargs["id"]] = {
            "func": func,
            "trigger": trigger,
            **kwargs,
        }

    def remove_job(self, job_id):
        self.removed_job_ids.append(job_id)
        self.jobs.pop(job_id, None)


class FakeEntryRepository:
    def __init__(self, completed=False):
        self.completed = completed

    def is_completed_today(self, habit_id, day):
        return self.completed


class FakePromptSender:
    def __init__(self):
        self.prompts = []

    def send(self, title, body):
        self.prompts.append((title, body))


class FailingPromptSender:
    def send(self, title, body):
        raise RuntimeError("prompt failed")


class FakeLogger:
    def __init__(self):
        self.exceptions = []
        self.infos = []

    def exception(self, message, *args):
        self.exceptions.append(message % args if args else message)

    def info(self, message, *args):
        self.infos.append(message % args if args else message)


def test_due_reminder_skips_prompt_when_habit_is_completed_today():
    reminder = SimpleNamespace(
        id=uuid.uuid4(),
        habit_id=uuid.uuid4(),
        habit=SimpleNamespace(name="Read 30 minutes"),
        reminder_time=time(8, 0),
        days=None,
    )
    prompt_sender = FakePromptSender()
    runner = ReminderJobRunner(
        FakeReminderRepository(reminder),
        FakeEntryRepository(completed=True),
        prompt_sender,
        today=lambda: date(2026, 5, 22),
    )

    sent = runner.send_due_prompt(reminder.id, time(8, 0))

    assert sent is False
    assert prompt_sender.prompts == []


def test_due_reminder_sends_prompt_for_active_incomplete_habit():
    reminder = SimpleNamespace(
        id=uuid.uuid4(),
        habit_id=uuid.uuid4(),
        habit=SimpleNamespace(name="Read 30 minutes"),
        reminder_time=time(8, 0),
        days=None,
    )
    prompt_sender = FakePromptSender()
    runner = ReminderJobRunner(
        FakeReminderRepository(reminder),
        FakeEntryRepository(completed=False),
        prompt_sender,
        today=lambda: date(2026, 5, 22),
    )

    sent = runner.send_due_prompt(reminder.id, time(8, 0))

    assert sent is True
    assert prompt_sender.prompts == [("Habit Reminder", "Read 30 minutes")]


def test_due_reminder_skips_stale_job_when_current_schedule_no_longer_matches():
    reminder = SimpleNamespace(
        id=uuid.uuid4(),
        habit_id=uuid.uuid4(),
        habit=SimpleNamespace(name="Read 30 minutes"),
        reminder_time=time(9, 0),
        days=[0],
    )
    prompt_sender = FakePromptSender()
    runner = ReminderJobRunner(
        FakeReminderRepository(reminder),
        FakeEntryRepository(completed=False),
        prompt_sender,
        today=lambda: date(2026, 5, 22),
    )

    sent = runner.send_due_prompt(reminder.id, time(8, 0))

    assert sent is False
    assert prompt_sender.prompts == []


def test_due_reminder_skips_when_today_is_not_selected():
    reminder = SimpleNamespace(
        id=uuid.uuid4(),
        habit_id=uuid.uuid4(),
        habit=SimpleNamespace(name="Read 30 minutes"),
        reminder_time=time(8, 0),
        days=[0],
    )
    prompt_sender = FakePromptSender()
    runner = ReminderJobRunner(
        FakeReminderRepository(reminder),
        FakeEntryRepository(completed=False),
        prompt_sender,
        today=lambda: date(2026, 5, 22),
    )

    sent = runner.send_due_prompt(reminder.id, time(8, 0))

    assert sent is False
    assert prompt_sender.prompts == []


def test_due_reminder_logs_prompt_failure_and_keeps_running():
    reminder = SimpleNamespace(
        id=uuid.uuid4(),
        habit_id=uuid.uuid4(),
        habit=SimpleNamespace(name="Read 30 minutes"),
        reminder_time=time(8, 0),
        days=None,
    )
    logger = FakeLogger()
    runner = ReminderJobRunner(
        FakeReminderRepository(reminder),
        FakeEntryRepository(completed=False),
        FailingPromptSender(),
        today=lambda: date(2026, 5, 22),
        logger=logger,
    )

    sent = runner.send_due_prompt(reminder.id, time(8, 0))

    assert sent is False
    assert logger.exceptions == [f"Failed to send Reminder prompt {reminder.id}"]


def test_due_reminder_logs_database_failure_and_skips_prompt():
    reminder_id = uuid.uuid4()
    prompt_sender = FakePromptSender()
    logger = FakeLogger()
    runner = ReminderJobRunner(
        FailingReminderRepository(),
        FakeEntryRepository(completed=False),
        prompt_sender,
        today=lambda: date(2026, 5, 22),
        logger=logger,
    )

    sent = runner.send_due_prompt(reminder_id, time(8, 0))

    assert sent is False
    assert prompt_sender.prompts == []
    assert logger.exceptions == [f"Failed to load Reminder {reminder_id}"]


def test_reconcile_schedules_one_cron_job_per_active_reminder():
    reminder = SimpleNamespace(
        id=uuid.uuid4(),
        habit_id=uuid.uuid4(),
        habit=SimpleNamespace(name="Read 30 minutes"),
        reminder_time=time(8, 30),
        days=[0, 2],
    )
    scheduler = FakeScheduler()
    job_runner = ReminderJobRunner(
        ActiveReminderRepository(reminder),
        FakeEntryRepository(),
        FakePromptSender(),
    )

    ReminderJobScheduler(
        ActiveReminderRepository(reminder),
        scheduler,
        job_runner,
    ).reconcile()

    job = scheduler.jobs[f"reminder:{reminder.id}"]
    assert job["trigger"] == "cron"
    assert job["hour"] == 8
    assert job["minute"] == 30
    assert job["day_of_week"] == "0,2"
    assert job["args"] == [reminder.id, time(8, 30)]


def test_reconcile_removes_stale_reminder_jobs():
    scheduler = FakeScheduler()
    stale_job_id = f"reminder:{uuid.uuid4()}"
    scheduler.jobs[stale_job_id] = {"id": stale_job_id}
    job_runner = ReminderJobRunner(
        ActiveReminderRepository(None),
        FakeEntryRepository(),
        FakePromptSender(),
    )

    ReminderJobScheduler(
        ActiveReminderRepository(None),
        scheduler,
        job_runner,
    ).reconcile()

    assert scheduler.removed_job_ids == [stale_job_id]
    assert scheduler.jobs == {}
