import datetime
import re
import threading

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog,
    QInputDialog,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

from Ward_DND_AI.config.config import log_exception
from Ward_DND_AI.utils import (
    auto_link_notes,
    get_all_folders,
    get_note_names,
    make_title_case_filename,
)
from Ward_DND_AI.utils.crash_handler import catch_and_report_crashes


class ChatController(QObject):
    ai_result_ready = pyqtSignal(str, int, int)  # answer, prompt tokens, response tokens

    def __init__(self, view, ctx, status_var=None):
        super().__init__()

        self.view = view

        self.ctx = ctx

        self.ai = ctx.ai

        self.storage = ctx.storage

        self.config = ctx.config

        self.status_var = status_var or self.view.status_label

        self.history = []

        self.last_answer = ""

        self.session_tokens = 0

        self.ai_result_ready.connect(self._handle_ai_result)

        self._bind_events()

    def _bind_events(self):
        self.view.chat_btn.clicked.connect(catch_and_report_crashes(self.on_chat))

        self.view.save_btn.clicked.connect(catch_and_report_crashes(self.on_save))

        self.view.split_btn.clicked.connect(catch_and_report_crashes(self.on_split))

        self.view.clear_btn.clicked.connect(catch_and_report_crashes(self.on_clear))

        self.view.preview_btn.clicked.connect(catch_and_report_crashes(self._on_preview))

    @catch_and_report_crashes
    def on_chat(self, *args, **kwargs):
        prompt = self.view.prompt_box.toPlainText().strip()

        if not prompt:
            self.status_var.setText("Please enter a prompt.")

            return

        self.view.save_btn.setEnabled(False)

        self.view.split_btn.setEnabled(False)

        self.status_var.setText("Thinking...")

        threading.Thread(target=self._run_ai, args=(prompt,), daemon=True).start()

    def _run_ai(self, prompt):
        try:
            answer, p_tokens, r_tokens = self.ai.ask(prompt)

        except Exception as e:
            self.status_var.setText(f"AI Error: {e}")

            log_exception("ChatController AI query failed", e)

            return

        self.ai_result_ready.emit(answer, p_tokens, r_tokens)

    @catch_and_report_crashes
    def _handle_ai_result(self, answer, p_tokens, r_tokens):
        self.session_tokens += p_tokens + r_tokens

        self.last_answer = answer

        self.history.append((self.view.prompt_box.toPlainText().strip(), answer))

        self.view.output_box.setReadOnly(False)

        self.view.output_box.setPlainText(answer)

        self.view.output_box.setReadOnly(True)

        self.view.history_text.setReadOnly(False)

        self.view.history_text.clear()

        for idx, (q, a) in enumerate(self.history, 1):
            self.view.history_text.append(f"{idx}. Q: {q}\nA: {a}\n")

        self.view.history_text.setReadOnly(True)

        self.status_var.setText(f"Done. Tokens: +{p_tokens}/{r_tokens}")

        self.view.save_btn.setEnabled(True)

        self.view.split_btn.setEnabled(True)

    @catch_and_report_crashes
    def on_save(self, *args, **kwargs):
        folders = get_all_folders(self.config.VAULT_PATH)

        folder, ok = QInputDialog.getItem(self.view, "Save Answer", "Select folder:", folders, 0, False)

        if not ok:
            return

        filename, ok = QInputDialog.getText(self.view, "File Name", "Enter file name (no extension):")

        if not ok or not filename.strip():
            self.status_var.setText("Save cancelled.")

            return

        filename = make_title_case_filename(filename.strip())

        rel = f"{folder}/{filename}.md" if folder else f"{filename}.md"

        content = f"# {filename}\n\n{self.last_answer}"

        try:
            self.storage.write_note(rel, content)

            self.status_var.setText(f"Saved answer to: {rel}")

        except Exception as e:
            QMessageBox.critical(self.view, "Save Failed", f"Could not save note: {e}")

            self.status_var.setText("Save error.")

            log_exception("ChatController save failed", e)

    @catch_and_report_crashes
    def on_split(self, *args, **kwargs):
        if not self.last_answer:
            self.status_var.setText("Nothing to split.")

            return

        folders = get_all_folders(self.config.VAULT_PATH)

        dest_folder, ok = QInputDialog.getItem(
            self.view,
            "Split & Save",
            "Select folder for split notes:",
            folders,
            0,
            False,
        )

        if not ok:
            return

        parts = [p for p in re.split(r"(?=^# )", self.last_answer, flags=re.MULTILINE) if p.strip()]

        existing = get_note_names(self.config.VAULT_PATH)

        count, errors = 0, []

        for chunk in parts:
            try:
                title_line, body = chunk.split("\n", 1)

                heading = title_line.lstrip("# ").strip()

                fname = make_title_case_filename(heading)

                rel = f"{dest_folder}/{fname}.md" if dest_folder else f"{fname}.md"

                note_content = (
                    f"# {heading}\n"
                    f"*Generated on {datetime.datetime.now():%Y-%m-%d %H:%M}*\n\n"
                    f"{auto_link_notes(body.strip(), existing)}"
                )

                self.storage.write_note(rel, note_content)

                count += 1

            except Exception as e:
                errors.append(heading)

                log_exception(f"Split failed for: {heading}", e)

        msg = f"Saved {count} notes." + (f" Failed: {', '.join(errors)}" if errors else "")

        QMessageBox.information(self.view, "Split & Save", msg)

        self.status_var.setText(msg)

    @catch_and_report_crashes
    def on_clear(self, *args, **kwargs):
        self.history.clear()

        self.view.prompt_box.clear()

        self.view.output_box.setReadOnly(False)

        self.view.output_box.clear()

        self.view.output_box.setReadOnly(True)

        self.view.history_text.setReadOnly(False)

        self.view.history_text.clear()

        self.view.history_text.setReadOnly(True)

        self.status_var.setText("History cleared.")

        self.view.save_btn.setEnabled(False)

        self.view.split_btn.setEnabled(False)

    @catch_and_report_crashes
    def _on_preview(self, *args, **kwargs):
        content = self.view.output_box.toPlainText()

        dlg = QDialog(self.view)

        dlg.setWindowTitle("AI Output Preview")

        dlg.resize(600, 400)

        layout = QVBoxLayout(dlg)

        textbox = QTextEdit()

        textbox.setPlainText(content)

        textbox.setReadOnly(True)

        layout.addWidget(textbox)

        btn = QPushButton("Close")

        btn.clicked.connect(dlg.accept)

        layout.addWidget(btn)

        dlg.exec()
