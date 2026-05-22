from datetime import date, timedelta


def calculate_habit_stats(
    completed_dates: set[date],
    created_at: date,
    today: date,
) -> dict:
    current_streak = 0
    day = today
    if day not in completed_dates:
        day -= timedelta(days=1)
    while day in completed_dates:
        current_streak += 1
        day -= timedelta(days=1)

    max_streak = 0
    if completed_dates:
        sorted_dates = sorted(completed_dates)
        max_streak = 1
        current_run = 1
        for index in range(1, len(sorted_dates)):
            if (sorted_dates[index] - sorted_dates[index - 1]).days == 1:
                current_run += 1
                max_streak = max(max_streak, current_run)
            else:
                current_run = 1

    total_days = (today - created_at).days + 1
    completion_rate = (
        round(len(completed_dates) / total_days * 100, 1)
        if total_days > 0 and completed_dates
        else 0.0
    )

    return {
        "current_streak": current_streak,
        "max_streak": max_streak,
        "completion_rate": completion_rate,
    }
