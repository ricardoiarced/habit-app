from datetime import date

from app.services.habit_stats import calculate_habit_stats


def test_habit_stats_are_zero_without_completions():
    assert calculate_habit_stats(
        completed_dates=set(),
        created_at=date(2026, 5, 20),
        today=date(2026, 5, 22),
    ) == {
        "current_streak": 0,
        "max_streak": 0,
        "completion_rate": 0.0,
    }


def test_current_streak_counts_through_yesterday_when_today_is_incomplete():
    stats = calculate_habit_stats(
        completed_dates={date(2026, 5, 20), date(2026, 5, 21)},
        created_at=date(2026, 5, 20),
        today=date(2026, 5, 22),
    )

    assert stats["current_streak"] == 2


def test_max_streak_uses_the_longest_run_across_gaps():
    stats = calculate_habit_stats(
        completed_dates={
            date(2026, 5, 1),
            date(2026, 5, 2),
            date(2026, 5, 4),
            date(2026, 5, 5),
            date(2026, 5, 6),
            date(2026, 5, 8),
        },
        created_at=date(2026, 5, 1),
        today=date(2026, 5, 8),
    )

    assert stats["max_streak"] == 3


def test_completion_rate_uses_creation_to_today_eligible_days():
    stats = calculate_habit_stats(
        completed_dates={date(2026, 5, 1), date(2026, 5, 3)},
        created_at=date(2026, 5, 1),
        today=date(2026, 5, 4),
    )

    assert stats["completion_rate"] == 50.0
