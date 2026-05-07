import glob
import os
from pathlib import Path

from PyQt6.QtCore import QObject, pyqtSlot

from Ward_DND_AI.utils.crash_handler import LOG_DIR, CrashHandler
from Ward_DND_AI.utils.logging_setup import APP_SESSION_LOG_HANDLER


class DebugController(QObject):
    def __init__(self, view, ctx):
        super().__init__()

        self.v = view

        self.ctx = ctx

        self.config = ctx.config

        # Connect crash logs tab signals

        self.v.refresh_crash_logs.connect(self.load_crash_logs)

        self.v.open_log_folder.connect(self.open_log_folder)

        self.v.copy_log.connect(self.copy_log_contents)

        self.v.delete_log.connect(self.delete_log_file)

        self.v.send_log.connect(self.send_log_file)

        self.v.crash_log_selected.connect(self.display_log_contents)

        # Runtime log tab signal wiring

        self.v.load_runtime_log.connect(self.load_runtime_log)

        self.v.clear_runtime_log.connect(self.clear_runtime_log)

        self.v.copy_runtime_log.connect(self.copy_runtime_log)

        self.v.save_runtime_log.connect(self.save_runtime_log)

        self.v.open_log_folder_runtime.connect(self.open_log_folder_runtime)

        # Runtime log tab (signals to be added as you wire up runtime log view)

        # Example: self.v.clear_runtime_log.connect(self.clear_runtime_log)

        self.crash_log_files = []

        self.current_log_path = None

        self.load_crash_logs()

    @pyqtSlot()
    def load_crash_logs(self):
        """Load all crash log files into the list."""

        log_paths = sorted(glob.glob(str(LOG_DIR / "crash_*.log")), key=os.path.getmtime, reverse=True)

        self.crash_log_files = log_paths

        self.v.set_crash_log_list([(os.path.basename(p), os.path.getmtime(p)) for p in log_paths])

        if log_paths:
            self.display_log_contents(0)  # Show the most recent log by default

        else:
            self.v.set_crash_log_contents("(No crash logs found)")

            self.current_log_path = None

    @pyqtSlot(int)
    def display_log_contents(self, index):
        """Display the contents of the selected crash log."""

        if not (0 <= index < len(self.crash_log_files)):
            self.v.set_crash_log_contents("(No log selected)")

            self.current_log_path = None

            return

        path = self.crash_log_files[index]

        try:
            text = Path(path).read_text(encoding="utf-8")

        except Exception as e:
            text = f"(Failed to read log: {e})"

        self.v.set_crash_log_contents(text)

        self.current_log_path = path

    @pyqtSlot()
    def copy_log_contents(self):
        """Copy current log contents to clipboard."""

        if self.current_log_path:
            text = Path(self.current_log_path).read_text(encoding="utf-8")

            self.v.copy_to_clipboard(text)

    @pyqtSlot()
    def open_log_folder(self):
        """Open the logs folder in file explorer."""

        import subprocess

        folder = str(LOG_DIR)

        if os.name == "nt":
            subprocess.Popen(f'explorer "{folder}"')

        else:
            subprocess.Popen(["xdg-open", folder])

    @pyqtSlot()
    def delete_log_file(self):
        """Delete the currently selected crash log file."""

        if self.current_log_path:
            try:
                os.remove(self.current_log_path)

                self.v.show_status_message(f"Deleted: {os.path.basename(self.current_log_path)}")

                self.load_crash_logs()

            except Exception as e:
                self.v.show_status_message(f"Failed to delete: {e}")

    @pyqtSlot()
    def send_log_file(self):
        """Send current log file via CrashHandler's email (if configured)."""

        if self.current_log_path:
            text = Path(self.current_log_path).read_text(encoding="utf-8")

            ok, msg = CrashHandler.send_crash_report_via_email(text, self.current_log_path)

            self.v.show_status_message(msg)

    # ---- RUNTIME LOG TAB SKELETON ----

    # Fill in after wiring up the runtime log view.

    # You can add: load_runtime_log, clear_runtime_log, etc.

    # ---- RUNTIME LOG TAB ----

    def load_runtime_log(self):
        """Load the in-memory session log into the runtime log viewer."""

        text = APP_SESSION_LOG_HANDLER.get_log_text()

        self.v.set_runtime_log_contents(text)

    def clear_runtime_log(self):
        """Clear the in-memory session log."""

        APP_SESSION_LOG_HANDLER.clear()

        self.v.set_runtime_log_contents("")

        self.v.show_status_message("Session log cleared.")

    def copy_runtime_log(self):
        """Copy in-memory session log to clipboard."""

        text = APP_SESSION_LOG_HANDLER.get_log_text()

        self.v.copy_to_clipboard(text)

        self.v.show_status_message("Session log copied to clipboard.")

    def save_runtime_log(self):
        """Save session log to file (let user choose location)."""

        from PyQt6.QtWidgets import QFileDialog

        text = APP_SESSION_LOG_HANDLER.get_log_text()

        fname, _ = QFileDialog.getSaveFileName(self.v, "Save Session Log", "session_log.txt", "Text Files (*.txt)")

        if fname:
            with open(fname, "w", encoding="utf-8") as f:
                f.write(text)

            self.v.show_status_message(f"Session log saved to: {fname}")

    def open_log_folder_runtime(self):
        """Open the logs folder in file explorer."""

        self.open_log_folder()  # Re-use method
