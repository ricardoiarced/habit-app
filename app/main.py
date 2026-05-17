import flet as ft
from app.database import SessionLocal
from app.services.habit_service import HabitService
from app.views.habit_list_view import habit_list_view


def main(page: ft.Page):
    print(">>> main(page) ejecutado — la sesión del navegador conectó")
    page.title = "Habit App"
    page.theme_mode = ft.ThemeMode.LIGHT

    try:
        session = SessionLocal()
        service = HabitService(session)
        print(">>> Sesión de BD creada, consultando hábitos...")

        view = habit_list_view(page, service)
        print(">>> View construida, montándola en page.views")

        page.views.clear()
        page.views.append(view)
        page.update()
        print(">>> page.update() llamado. Si no ves nada en el navegador a partir de aquí, el problema es del cliente JS, no de Python.")
    except Exception as e:
        # Si algo revienta dentro de main, lo verás en consola en lugar de en pantalla en blanco.
        print(f"!!! ERROR en main: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        page.views[0].controls = [ft.Text(f"Error: {e}", color=ft.Colors.RED)]
        page.update()


ft.run(main, view=ft.AppView.WEB_BROWSER)