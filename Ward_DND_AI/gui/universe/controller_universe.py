from PyQt6.QtCore import QObject
from PyQt6.QtWidgets import QInputDialog, QMessageBox

from Ward_DND_AI.utils.crash_handler import catch_and_report_crashes


class UniverseController(QObject):
    def __init__(self, view, ctx, status_var=None):
        super().__init__()

        self.view = view

        self.ctx = ctx

        self.ai = ctx.ai

        self.storage = ctx.storage

        self.config = ctx.config

        self.status_var = status_var

        self.events = []

        self._refresh_event_list()

        # Wire up buttons

        self.view.add_btn.clicked.connect(catch_and_report_crashes(self.add_event))

        self.view.edit_btn.clicked.connect(catch_and_report_crashes(self.edit_event))

        self.view.delete_btn.clicked.connect(catch_and_report_crashes(self.delete_event))

    def _refresh_event_list(self):
        self.view.event_list.clear()

        for ev in self.events:
            self.view.event_list.append(ev)

    @catch_and_report_crashes
    def add_event(self):
        text, ok = QInputDialog.getText(self.view, "New Event", "Event description:")

        if ok and text:
            self.events.append(text)

            self._refresh_event_list()

    @catch_and_report_crashes
    def edit_event(self):
        cursor = self.view.event_list.textCursor()

        current = cursor.selectedText()

        if not current:
            QMessageBox.warning(self.view, "Edit Event", "Select text to edit.")

            return

        new_text, ok = QInputDialog.getText(self.view, "Edit Event", "Event description:", text=current)

        if ok and new_text:
            cursor.insertText(new_text)

            self.events = self.view.event_list.toPlainText().split("\n")

    @catch_and_report_crashes
    def delete_event(self):
        cursor = self.view.event_list.textCursor()

        sel = cursor.selectedText()

        if not sel:
            QMessageBox.warning(self.view, "Delete Event", "Select text to delete.")

            return

        resp = QMessageBox.question(
            self.view,
            "Delete Event",
            f"Remove selected event?\n\n{sel}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if resp == QMessageBox.StandardButton.Yes:
            cursor.removeSelectedText()

            self.events = self.view.event_list.toPlainText().split("\n")
