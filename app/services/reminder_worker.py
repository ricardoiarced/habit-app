from datetime import date, time
import logging
import uuid


class ReminderJobRunner:
    def __init__(
        self,
        reminder_repository,
        entry_repository,
        prompt_sender,
        today=date.today,
        logger: logging.Logger | None = None,
    ):
        self.reminder_repository = reminder_repository
        self.entry_repository = entry_repository
        self.prompt_sender = prompt_sender
        self.today = today
        self.logger = logger or logging.getLogger(__name__)

    def send_due_prompt(self, reminder_id: uuid.UUID, scheduled_time: time) -> bool:
        try:
            reminder = self.reminder_repository.get_active(reminder_id)
        except Exception:
            self.logger.exception("Failed to load Reminder %s", reminder_id)
            return False
        if reminder is None:
            self.logger.info("Skipped Reminder prompt %s because it is inactive or missing", reminder_id)
            return False
        today = self.today()
        if reminder.reminder_time != scheduled_time:
            self.logger.info("Skipped stale Reminder job %s", reminder.id)
            return False
        if reminder.days is not None and today.weekday() not in reminder.days:
            self.logger.info("Skipped Reminder prompt %s because today is not selected", reminder.id)
            return False
        if self.entry_repository.is_completed_today(reminder.habit_id, today):
            self.logger.info("Skipped Reminder prompt %s because Habit is completed today", reminder.id)
            return False
        try:
            self.prompt_sender.send("Habit Reminder", reminder.habit.name)
        except Exception:
            self.logger.exception("Failed to send Reminder prompt %s", reminder.id)
            return False
        self.logger.info("Sent Reminder prompt %s", reminder.id)
        return True


class ReminderJobScheduler:
    job_prefix = "reminder:"

    def __init__(
        self,
        reminder_repository,
        scheduler,
        job_runner: ReminderJobRunner,
        logger: logging.Logger | None = None,
    ):
        self.reminder_repository = reminder_repository
        self.scheduler = scheduler
        self.job_runner = job_runner
        self.logger = logger or logging.getLogger(__name__)

    def reconcile(self) -> bool:
        try:
            reminders = self.reminder_repository.list_active()
        except Exception:
            self.logger.exception("Failed to load active Reminders")
            return False

        desired_job_ids = {self._job_id(reminder.id) for reminder in reminders}
        for job in self.scheduler.get_jobs():
            if job.id.startswith(self.job_prefix) and job.id not in desired_job_ids:
                self.scheduler.remove_job(job.id)

        for reminder in reminders:
            job_kwargs = {
                "id": self._job_id(reminder.id),
                "replace_existing": True,
                "hour": reminder.reminder_time.hour,
                "minute": reminder.reminder_time.minute,
                "args": [reminder.id, reminder.reminder_time],
            }
            if reminder.days is not None:
                job_kwargs["day_of_week"] = ",".join(str(day) for day in reminder.days)
            self.scheduler.add_job(
                self.job_runner.send_due_prompt,
                "cron",
                **job_kwargs,
            )
        self.logger.info("Reconciled %s active Reminders", len(reminders))
        return True

    def _job_id(self, reminder_id: uuid.UUID) -> str:
        return f"{self.job_prefix}{reminder_id}"
