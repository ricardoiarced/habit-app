import base64

from app.services.desktop_prompt_sender import DesktopPromptSender


class FakePlyerNotification:
    def __init__(self):
        self.calls = []

    def notify(self, **kwargs):
        self.calls.append(kwargs)


class CapturingCommandRunner:
    def __init__(self):
        self.commands = []

    def __call__(self, command, **kwargs):
        self.commands.append((command, kwargs))


def test_desktop_prompt_uses_plyer_outside_wsl():
    notification = FakePlyerNotification()
    sender = DesktopPromptSender(
        notification=notification,
        environment={},
        platform_release="6.6.0-linux",
    )

    sender.send("Habit Reminder", "Read 30 minutes")

    assert notification.calls == [
        {
            "title": "Habit Reminder",
            "message": "Read 30 minutes",
            "app_name": "Habit App",
        }
    ]


def test_desktop_prompt_uses_windows_prompt_when_running_in_wsl():
    command_runner = CapturingCommandRunner()
    sender = DesktopPromptSender(
        command_runner=command_runner,
        environment={"WSL_INTEROP": "1"},
        platform_release="6.6.114.1-microsoft-standard-WSL2",
        find_executable=lambda name: f"/mnt/c/Windows/System32/{name}",
    )

    sender.send("Habit Reminder", "Read 30 minutes")

    command, kwargs = command_runner.commands[0]
    assert command[0].endswith("powershell.exe")
    encoded_script = command[command.index("-EncodedCommand") + 1]
    script = base64.b64decode(encoded_script).decode("utf-16le")
    assert "Habit Reminder" in script
    assert "Read 30 minutes" in script
    assert kwargs["timeout"] == 15
