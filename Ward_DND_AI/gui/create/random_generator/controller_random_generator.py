from PyQt6.QtCore import QObject

from Ward_DND_AI.utils.crash_handler import catch_and_report_crashes


class RandomGeneratorController(QObject):
    def __init__(self, view, ctx, status_var=None):
        super().__init__()

        self.view = view

        self.ctx = ctx

        self.ai = ctx.ai

        self.storage = ctx.storage

        self.config = ctx.config

        self.status_var = status_var  # optional for status bar updates

        self.view.generate_btn.clicked.connect(catch_and_report_crashes(self.on_generate))

        self.view.save_btn.clicked.connect(catch_and_report_crashes(self.on_save))

    @catch_and_report_crashes
    def on_generate(self, *args, **kwargs):
        prompt = self.view.prompt_entry.text().strip()

        if not prompt:
            self._show_output("[Please enter a prompt]")
            return

        selected_type = self.view.type_menu.currentText()
        full_prompt = (
            f"You are a creative D&D game master assistant. Generate detailed, imaginative content.\n"
            f"Type: {selected_type}\n"
            f"Request: {prompt}\n\n"
            f"Provide a well-formatted, ready-to-use result."
        )
        result, _, _ = self.ai.ask(full_prompt)
        self._show_output(result)

    @catch_and_report_crashes
    def on_save(self):
        import os

        from PyQt6.QtWidgets import QInputDialog

        content = self.view.output_text.toPlainText().strip()
        if not content:
            self._show_output("[No content to save — generate something first]")
            return

        title, ok = QInputDialog.getText(self.view, "Save to Vault", "Note title:")
        if not ok or not title.strip():
            return
        title = title.strip()

        try:
            vault_path = getattr(self.config, "VAULT_PATH", ".")
            path = os.path.join(vault_path, title + ".md")
            self.storage.write_note(path, content)
            self._show_output(f"[Saved: {title}.md]")
        except Exception as exc:
            self._show_output(f"[Save failed: {exc}]")

    def _show_output(self, text: str):
        self.view.output_text.setPlainText(text)
