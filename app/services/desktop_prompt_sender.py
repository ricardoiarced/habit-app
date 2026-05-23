import base64
import os
import platform
import shutil
import subprocess


class DesktopPromptSender:
    def __init__(
        self,
        notification=None,
        command_runner=subprocess.run,
        environment=None,
        platform_release=None,
        find_executable=shutil.which,
    ):
        self.notification = notification
        self.command_runner = command_runner
        self.environment = os.environ if environment is None else environment
        self.platform_release = platform.release() if platform_release is None else platform_release
        self.find_executable = find_executable

    def send(self, title: str, body: str) -> None:
        powershell = self.find_executable("powershell.exe")
        if self._is_wsl() and powershell:
            self._send_windows_prompt(powershell, title, body)
            return

        notification = self.notification
        if notification is None:
            from plyer import notification

        notification.notify(
            title=title,
            message=body,
            app_name="Habit App",
        )

    def _is_wsl(self) -> bool:
        release = self.platform_release.lower()
        return bool(self.environment.get("WSL_INTEROP")) or "microsoft" in release

    def _send_windows_prompt(self, powershell: str, title: str, body: str) -> None:
        title = self._powershell_string(title)
        body = self._powershell_string(body)
        script = f"""
$Title = {title}
$Body = {body}
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
$notification = New-Object System.Windows.Forms.NotifyIcon
$notification.Icon = [System.Drawing.SystemIcons]::Information
$notification.BalloonTipIcon = [System.Windows.Forms.ToolTipIcon]::Info
$notification.BalloonTipTitle = $Title
$notification.BalloonTipText = $Body
$notification.Visible = $true
$notification.ShowBalloonTip(10000)
Start-Sleep -Seconds 11
$notification.Dispose()
"""
        encoded_script = base64.b64encode(script.encode("utf-16le")).decode("ascii")
        self.command_runner(
            [
                powershell,
                "-NoProfile",
                "-NonInteractive",
                "-WindowStyle",
                "Hidden",
                "-EncodedCommand",
                encoded_script,
            ],
            check=True,
            timeout=15,
        )

    def _powershell_string(self, value: str) -> str:
        return "'" + value.replace("'", "''") + "'"
