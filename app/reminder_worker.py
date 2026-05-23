import logging
import select
import tempfile
import threading
import time
from pathlib import Path

from apscheduler.schedulers.background import BackgroundScheduler
from filelock import FileLock, Timeout
from sqlalchemy import text

from app.database import SessionLocal, engine
from app.repositories.entry_repository import EntryRepository
from app.repositories.reminder_repository import ReminderRepository
from app.services.desktop_prompt_sender import DesktopPromptSender
from app.services.reminder_worker import ReminderJobRunner, ReminderJobScheduler


REMINDER_CHANGE_CHANNEL = "reminder_changes"
SYNC_INTERVAL_SECONDS = 30


class SessionReminderJobRunner:
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.prompt_sender = DesktopPromptSender()

    def send_due_prompt(self, reminder_id, scheduled_time) -> bool:
        session = SessionLocal()
        try:
            runner = ReminderJobRunner(
                ReminderRepository(session),
                EntryRepository(session),
                self.prompt_sender,
                logger=self.logger,
            )
            return runner.send_due_prompt(reminder_id, scheduled_time)
        finally:
            session.close()


def worker_directory() -> Path:
    directory = Path(tempfile.gettempdir()) / "habit-app"
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def configure_logging(directory: Path) -> logging.Logger:
    logger = logging.getLogger("habit_app.reminder_worker")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    file_handler = logging.FileHandler(directory / "reminder-worker.log")
    file_handler.setFormatter(formatter)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger


def reconcile_jobs(
    scheduler: BackgroundScheduler,
    job_runner: SessionReminderJobRunner,
    logger: logging.Logger,
) -> bool:
    session = SessionLocal()
    try:
        return ReminderJobScheduler(
            ReminderRepository(session),
            scheduler,
            job_runner,
            logger=logger,
        ).reconcile()
    finally:
        session.close()


def listen_for_reminder_changes(on_change, logger: logging.Logger) -> None:
    while True:
        try:
            with engine.connect() as connection:
                connection = connection.execution_options(isolation_level="AUTOCOMMIT")
                connection.execute(text(f"LISTEN {REMINDER_CHANGE_CHANNEL}"))
                raw_connection = connection.connection.driver_connection

                while True:
                    ready, _, _ = select.select(
                        [raw_connection],
                        [],
                        [],
                        SYNC_INTERVAL_SECONDS,
                    )
                    if not ready:
                        continue
                    raw_connection.poll()
                    while raw_connection.notifies:
                        raw_connection.notifies.pop(0)
                        on_change()
        except Exception:
            logger.exception("Reminder change listener failed")
            time.sleep(SYNC_INTERVAL_SECONDS)


def run_worker() -> None:
    directory = worker_directory()
    logger = configure_logging(directory)
    lock = FileLock(directory / "reminder-worker.lock")

    try:
        with lock.acquire(timeout=0):
            scheduler = BackgroundScheduler()
            job_runner = SessionReminderJobRunner(logger)

            scheduler.add_job(
                lambda: reconcile_jobs(scheduler, job_runner, logger),
                "interval",
                seconds=SYNC_INTERVAL_SECONDS,
                id="reminder_reconcile",
                replace_existing=True,
            )
            scheduler.start()
            reconcile_jobs(scheduler, job_runner, logger)

            listener = threading.Thread(
                target=listen_for_reminder_changes,
                args=(lambda: reconcile_jobs(scheduler, job_runner, logger), logger),
                daemon=True,
            )
            listener.start()
            logger.info("Reminder worker started")

            while True:
                time.sleep(60)
    except Timeout:
        logger.info("Reminder worker already running")
    except KeyboardInterrupt:
        logger.info("Reminder worker stopped")


if __name__ == "__main__":
    run_worker()
