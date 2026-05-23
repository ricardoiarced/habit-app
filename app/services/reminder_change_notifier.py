from sqlalchemy import text
from sqlalchemy.orm import Session


class PostgresReminderChangeNotifier:
    def __init__(self, session: Session):
        self.session = session

    def notify(self) -> None:
        self.session.execute(text("NOTIFY reminder_changes"))
        self.session.commit()
