# Milestone 4: Habit Stats UI

## What We Built

- Added a per-habit Habit Stats screen opened from a stats icon on each habit row.
- Showed the selected Habit name, today's Completion action, and three Habit Stats: Current Streak, Max Streak, and Completion Rate.
- Added an undo path for today's Completion so accidental marks can be reversed from the stats screen.
- Kept Habit Stats scoped to one selected Habit rather than a global dashboard.
- Created `CONTEXT.md` to record the resolved domain language: Habit, Completion, Habit Stats, Current Streak, Max Streak, Completion Rate, and Eligible Day.

## Implementation Notes

- Extracted pure Habit Stats calculation into `app/services/habit_stats.py`.
- Updated `StreakCalculator` to use the tested pure calculation while keeping `HabitService.get_stats()` as the app-facing API.
- Added `pytest` and tests in `tests/test_habit_stats.py` for the agreed Habit Stats behaviors.
- Updated the existing Flet habit list view to push a separate stats view onto `page.views`.
- Added a today Completion status lookup and toggle action to the stats view.

## Problems And Fixes

- There was no existing project glossary or milestone documentation. We created `CONTEXT.md` only after resolving the first terms.
- `pytest` was not installed in the virtualenv. We added it to `requirements.txt` and installed requirements before running tests.
- The first TDD test failed because `app.services.habit_stats` did not exist. We added the module and grew it one behavior at a time.
- Stats calculation was coupled to database access and `date.today()`, which made deterministic tests awkward. We extracted `calculate_habit_stats()` so tests can pass explicit dates.
- `HabitService.is_completed_today()` called `EntryRepository.is_completed_today()` without the required `day` argument. We fixed the service call.
- `EntryRepository.is_completed_today()` accepted a `day` argument but ignored it and used `date.today()` internally. We fixed it to use the provided day.

## Verification

- `python -m pytest` passed with 4 tests.
- `python -m py_compile app/services/habit_stats.py app/services/streak_calculator.py app/repositories/entry_repository.py app/services/habit_service.py app/views/habit_list_view.py` passed.
- Flet icon and control construction checks passed for the new controls.

## Not Done

- No global dashboard was added.
- No past-date Completion editing was added.
- No ADR was created because the decisions were reversible and not surprising enough to justify one.
