import flet as ft
from app.database import SessionLocal
from app.services.habit_service import HabitService
from app.views.habit_list_view import habit_list_view


def main(page: ft.Page):
    print(">>> main(page) executed — browser session got connected")
    page.title = "Habit App"
    page.theme_mode = ft.ThemeMode.LIGHT

    try:
        session = SessionLocal()
        service = HabitService(session)
        print(">>> DB session created, querying habits...")

        view = habit_list_view(page, service)
        print(">>> View built, mounting it on page.views")

        page.views.clear()
        page.views.append(view)
        page.update()
        print(">>> page.update() called. If you don't see anything from now on, the JS client is the problem, not Python.")
    except Exception as e:
        print(f"!!! ERROR en main: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        page.views[0].controls = [ft.Text(f"Error: {e}", color=ft.Colors.RED)]
        page.update()


ft.run(main, view=ft.AppView.WEB_BROWSER)