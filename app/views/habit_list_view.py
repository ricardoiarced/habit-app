import flet as ft
from app.services.habit_service import HabitService
from app.services.reminder_service import ReminderService


def habit_list_view(
    page: ft.Page,
    service: HabitService,
    reminder_service: ReminderService | None = None,
    start_reminder_worker=None,
) -> ft.View:
    # --- state
    habits = service.get_habits()
    new_habit_field = ft.TextField(hint_text="e.g. Read 30 minutes", expand=True)

    def stat_card(label: str, value: str, icon: str) -> ft.Card:
        return ft.Card(
            content=ft.Container(
                content=ft.Row(
                    [
                        ft.Icon(icon, color=ft.Colors.BLUE_400, size=32),
                        ft.Column(
                            [
                                ft.Text(label, color=ft.Colors.GREY_600, size=13),
                                ft.Text(value, size=24, weight=ft.FontWeight.BOLD),
                            ],
                            spacing=2,
                        ),
                    ],
                    spacing=16,
                ),
                padding=16,
            )
        )

    weekday_labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    def format_reminder_time(reminder_time) -> str:
        return reminder_time.strftime("%H:%M")

    def format_reminder_days(days: list[int] | None) -> str:
        if days is None:
            return "Every day"
        return ", ".join(weekday_labels[day] for day in days)

    def show_error(message: str):
        page.show_dialog(
            ft.AlertDialog(
                title=ft.Text("Reminder Error"),
                content=ft.Text(message),
                actions=[ft.TextButton("OK", on_click=lambda e: page.pop_dialog())],
            )
        )

    def open_stats(habit):
        stats_container = ft.Container(padding=20, expand=True)

        def close_stats(e):
            if len(page.views) > 1:
                page.views.pop()
            page.update()

        def on_toggle_today(e):
            service.toggle_today(habit.id)
            refresh_stats()

        def refresh_stats():
            stats = service.get_stats(habit)
            completed_today = service.is_completed_today(habit.id)
            action_label = (
                "Undo today's Completion"
                if completed_today
                else "Mark today complete"
            )
            action_icon = ft.Icons.UNDO if completed_today else ft.Icons.CHECK_CIRCLE_OUTLINE
            status_text = (
                "Today is completed."
                if completed_today
                else "Today is not completed yet."
            )

            stats_container.content = ft.Column(
                [
                    ft.Text(habit.name, size=28, weight=ft.FontWeight.BOLD),
                    ft.Card(
                        content=ft.Container(
                            content=ft.Column(
                                [
                                    ft.Text(
                                        "Today's Completion",
                                        size=16,
                                        weight=ft.FontWeight.BOLD,
                                    ),
                                    ft.Text(status_text, color=ft.Colors.GREY_600),
                                    ft.ElevatedButton(
                                        action_label,
                                        icon=action_icon,
                                        on_click=on_toggle_today,
                                    ),
                                ],
                                spacing=10,
                            ),
                            padding=16,
                        )
                    ),
                    stat_card(
                        "Current Streak",
                        f"{stats['current_streak']} days",
                        ft.Icons.LOCAL_FIRE_DEPARTMENT,
                    ),
                    stat_card(
                        "Max Streak",
                        f"{stats['max_streak']} days",
                        ft.Icons.EMOJI_EVENTS,
                    ),
                    stat_card(
                        "Completion Rate",
                        f"{stats['completion_rate']}%",
                        ft.Icons.PERCENT,
                    ),
                ],
                spacing=12,
                scroll=ft.ScrollMode.AUTO,
            )
            page.update()

        stats_view = ft.View(
            route=f"/habits/{habit.id}/stats",
            appbar=ft.AppBar(
                leading=ft.IconButton(
                    icon=ft.Icons.ARROW_BACK,
                    on_click=close_stats,
                ),
                title=ft.Text("Habit Stats", weight=ft.FontWeight.BOLD),
                bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
            ),
            controls=[stats_container],
        )

        page.views.append(stats_view)
        refresh_stats()

    def open_reminders(habit):
        if reminder_service is None:
            show_error("Reminders are not available.")
            return

        reminders_container = ft.Column(expand=True)

        def close_reminders(e):
            if len(page.views) > 1:
                page.views.pop()
            page.update()

        def refresh_reminders():
            reminders = reminder_service.list_reminders(habit.id)
            if not reminders:
                reminder_list = ft.Text(
                    "No Reminders yet. Add one to be prompted about this Habit.",
                    color=ft.Colors.GREY_500,
                )
            else:
                reminder_list = ft.Column(
                    [
                        ft.Card(
                            content=ft.ListTile(
                                leading=ft.Icon(ft.Icons.ALARM),
                                title=ft.Text(format_reminder_time(reminder.reminder_time)),
                                subtitle=ft.Text(format_reminder_days(reminder.days)),
                                trailing=ft.Row(
                                    [
                                        ft.IconButton(
                                            icon=ft.Icons.EDIT_OUTLINED,
                                            tooltip="Edit Reminder",
                                            on_click=lambda e, r=reminder: show_reminder_dialog(r),
                                        ),
                                        ft.IconButton(
                                            icon=ft.Icons.DELETE_OUTLINE,
                                            icon_color=ft.Colors.RED_400,
                                            tooltip="Delete Reminder",
                                            on_click=lambda e, r=reminder: confirm_delete_reminder(r),
                                        ),
                                    ],
                                    spacing=0,
                                    width=96,
                                ),
                            )
                        )
                        for reminder in reminders
                    ],
                    spacing=8,
                )

            reminders_container.controls = [
                ft.Text(habit.name, size=28, weight=ft.FontWeight.BOLD),
                ft.ElevatedButton(
                    "Add Reminder",
                    icon=ft.Icons.ADD_ALARM,
                    on_click=lambda e: show_reminder_dialog(),
                ),
                ft.Divider(),
                reminder_list,
            ]
            page.update()

        def show_reminder_dialog(reminder=None):
            selected_time = {"value": reminder.reminder_time if reminder else None}
            every_day = ft.Checkbox(value=reminder is None or reminder.days is None)
            weekday_checks = [
                ft.Checkbox(
                    label=label,
                    value=reminder is not None and reminder.days is not None and index in reminder.days,
                )
                for index, label in enumerate(weekday_labels)
            ]
            time_label = ft.Text(
                format_reminder_time(selected_time["value"])
                if selected_time["value"]
                else "No time selected",
                color=ft.Colors.GREY_700,
            )
            error_text = ft.Text("", color=ft.Colors.RED_400)

            def sync_day_controls():
                for checkbox in weekday_checks:
                    checkbox.disabled = bool(every_day.value)

            def on_every_day_changed(e):
                sync_day_controls()
                page.update()

            every_day.label = "Every day"
            every_day.on_change = on_every_day_changed
            sync_day_controls()

            def on_time_changed(e):
                selected_time["value"] = e.control.value
                time_label.value = format_reminder_time(e.control.value)
                page.update()

            time_picker = ft.TimePicker(
                value=selected_time["value"],
                help_text="Pick Reminder time",
                confirm_text="Save time",
                cancel_text="Cancel",
                hour_format=ft.TimePickerHourFormat.H24,
                on_change=on_time_changed,
            )

            def open_time_picker(e):
                page.show_dialog(time_picker)

            def save_reminder(e):
                try:
                    if selected_time["value"] is None:
                        raise ValueError("Pick a Reminder time.")
                    days = None
                    if not every_day.value:
                        days = [
                            index
                            for index, checkbox in enumerate(weekday_checks)
                            if checkbox.value
                        ]
                    if reminder is None:
                        reminder_service.create_reminder(
                            habit.id,
                            selected_time["value"],
                            days=days,
                        )
                        if start_reminder_worker:
                            start_reminder_worker()
                    else:
                        reminder_service.update_reminder(
                            reminder.id,
                            selected_time["value"],
                            days=days,
                        )
                    page.pop_dialog()
                    refresh_reminders()
                except ValueError as ex:
                    error_text.value = str(ex)
                    page.update()
                except Exception as ex:
                    error_text.value = f"Could not save Reminder: {ex}"
                    page.update()

            dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text("Edit Reminder" if reminder else "Add Reminder"),
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                ft.ElevatedButton(
                                    "Pick time",
                                    icon=ft.Icons.SCHEDULE,
                                    on_click=open_time_picker,
                                ),
                                time_label,
                            ],
                            alignment=ft.MainAxisAlignment.START,
                        ),
                        every_day,
                        ft.Text("Selected weekdays", weight=ft.FontWeight.BOLD),
                        ft.Row(weekday_checks[:4], wrap=True),
                        ft.Row(weekday_checks[4:], wrap=True),
                        error_text,
                    ],
                    tight=True,
                    spacing=8,
                ),
                actions=[
                    ft.TextButton("Cancel", on_click=lambda e: page.pop_dialog()),
                    ft.ElevatedButton("Save", on_click=save_reminder),
                ],
            )
            page.show_dialog(dialog)

        def confirm_delete_reminder(reminder):
            def delete_reminder(e):
                try:
                    reminder_service.delete_reminder(reminder.id)
                    page.pop_dialog()
                    refresh_reminders()
                except Exception as ex:
                    page.pop_dialog()
                    show_error(f"Could not delete Reminder: {ex}")

            page.show_dialog(
                ft.AlertDialog(
                    modal=True,
                    title=ft.Text("Delete Reminder?"),
                    content=ft.Text(
                        f"Delete the {format_reminder_time(reminder.reminder_time)} Reminder?"
                    ),
                    actions=[
                        ft.TextButton("Cancel", on_click=lambda e: page.pop_dialog()),
                        ft.ElevatedButton(
                            "Delete",
                            icon=ft.Icons.DELETE_OUTLINE,
                            on_click=delete_reminder,
                        ),
                    ],
                )
            )

        reminders_view = ft.View(
            route=f"/habits/{habit.id}/reminders",
            appbar=ft.AppBar(
                leading=ft.IconButton(
                    icon=ft.Icons.ARROW_BACK,
                    on_click=close_reminders,
                ),
                title=ft.Text("Reminders", weight=ft.FontWeight.BOLD),
                bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
            ),
            controls=[ft.Container(content=reminders_container, padding=20, expand=True)],
        )

        page.views.append(reminders_view)
        refresh_reminders()

    # --- build the list
    def build_habit_list():
        if not habits:
            return ft.Text(
                "You don't have any habits yet. Add one!",
                color=ft.Colors.GREY_500,
            )
        return ft.Column(
            [
                ft.Card(
                    content=ft.ListTile(
                        leading=ft.Icon(
                            ft.Icons.CIRCLE,
                            color=habit.color or "#4A90D9",
                        ),
                        title=ft.Text(habit.name, size=16),
                        trailing=ft.Row(
                            [
                                ft.IconButton(
                                    icon=ft.Icons.BAR_CHART,
                                    tooltip="View Habit Stats",
                                    on_click=lambda e, h=habit: open_stats(h),
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.ALARM,
                                    tooltip="Manage Reminders",
                                    on_click=lambda e, h=habit: open_reminders(h),
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.DELETE_OUTLINE,
                                    icon_color=ft.Colors.RED_400,
                                    on_click=lambda e, h=habit: on_delete(h.id),
                                ),
                            ],
                            spacing=0,
                            width=144,
                        ),
                    )
                )
                for habit in habits
            ],
            spacing=8,
        )

    habit_list_container = ft.Column([build_habit_list()], expand=True)

    def refresh_list():
        habit_list_container.controls = [build_habit_list()]
        page.update()

    # --- Events
    def on_add(e):
        try:
            habit = service.add_habit(new_habit_field.value or "")
            habits.append(habit)
            new_habit_field.value = ""
            refresh_list()
        except ValueError as ex:
            page.show_dialog(ft.SnackBar(ft.Text(str(ex))))

    def on_delete(habit_id):
        service.delete_habit(habit_id)
        habits[:] = [h for h in habits if h.id != habit_id]
        refresh_list()

    # --- Layout
    return ft.View(
        route="/",
        appbar=ft.AppBar(
            title=ft.Text("My Habits", weight=ft.FontWeight.BOLD),
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
        ),
        controls=[
            ft.Container(
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                new_habit_field,
                                ft.ElevatedButton(
                                    "Add",
                                    icon=ft.Icons.ADD,
                                    on_click=on_add,
                                ),
                            ]
                        ),
                        ft.Divider(),
                        habit_list_container,
                    ],
                    expand=True,
                ),
                padding=20,
                expand=True,
            ),
        ],
    )
