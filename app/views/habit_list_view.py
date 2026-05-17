import flet as ft
from app.services.habit_service import HabitService


def habit_list_view(page: ft.Page, service: HabitService) -> ft.View:
    # --- state
    habits = service.get_habits()
    new_habit_field = ft.TextField(hint_text="e.g. Read 30 minutes", expand=True)

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
                        trailing=ft.IconButton(
                            icon=ft.Icons.DELETE_OUTLINE,
                            icon_color=ft.Colors.RED_400,
                            on_click=lambda e, h=habit: on_delete(h.id),
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