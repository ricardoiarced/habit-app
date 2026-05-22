import flet as ft
from app.services.habit_service import HabitService


def habit_list_view(page: ft.Page, service: HabitService) -> ft.View:
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
                                    icon=ft.Icons.DELETE_OUTLINE,
                                    icon_color=ft.Colors.RED_400,
                                    on_click=lambda e, h=habit: on_delete(h.id),
                                ),
                            ],
                            spacing=0,
                            width=96,
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
