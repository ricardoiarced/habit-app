"""add reminder constraints

Revision ID: 4c2df54f2a71
Revises: 19251df4605c
Create Date: 2026-05-22 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "4c2df54f2a71"
down_revision: Union[str, Sequence[str], None] = "19251df4605c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_check_constraint(
        "ck_reminders_days_canonical",
        "reminders",
        """
        days IS NULL OR (
            cardinality(days) BETWEEN 1 AND 6
            AND array_position(days, NULL) IS NULL
            AND days <@ ARRAY[0,1,2,3,4,5,6]::integer[]
        )
        """,
    )
    op.execute(
        """
        CREATE UNIQUE INDEX uq_reminders_habit_time_days
        ON reminders (
            habit_id,
            reminder_time,
            COALESCE(days, ARRAY[]::integer[])
        )
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP INDEX IF EXISTS uq_reminders_habit_time_days")
    op.drop_constraint(
        "ck_reminders_days_canonical",
        "reminders",
        type_="check",
    )
