import flet as ft
from app.database import SessionLocal
from app.repositories.reminder_repository import ReminderRepository
from app.services.habit_service import HabitService
from app.services.reminder_change_notifier import PostgresReminderChangeNotifier
from app.services.reminder_service import ReminderService
from app.services.reminder_worker_launcher import launch_detached_reminder_worker
from app.views.habit_list_view import habit_list_view


def main(page: ft.Page):
    print(">>> main(page) executed — browser session got connected")
    page.title = "Habit App"
    page.theme_mode = ft.ThemeMode.LIGHT

    try:
        session = SessionLocal()
        service = HabitService(session)
        reminder_service = ReminderService(
            ReminderRepository(session),
            PostgresReminderChangeNotifier(session),
        )
        print(">>> DB session created, querying habits...")

        def start_reminder_worker():
            try:
                launch_detached_reminder_worker()
            except Exception as worker_error:
                page.show_dialog(
                    ft.AlertDialog(
                        title=ft.Text("Reminder Worker Error"),
                        content=ft.Text(str(worker_error)),
                        actions=[
                            ft.TextButton("OK", on_click=lambda e: page.pop_dialog())
                        ],
                    )
                )

        view = habit_list_view(
            page,
            service,
            reminder_service,
            start_reminder_worker,
        )
        print(">>> View built, mounting it on page.views")

        page.views.clear()
        page.views.append(view)
        page.update()
        if reminder_service.has_active_reminders():
            start_reminder_worker()
        print(">>> page.update() called. If you don't see anything from now on, the JS client is the problem, not Python.")
    except Exception as e:
        print(f"!!! ERROR en main: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        page.views[0].controls = [ft.Text(f"Error: {e}", color=ft.Colors.RED)]
        page.update()


ft.run(main, view=ft.AppView.WEB_BROWSER)
