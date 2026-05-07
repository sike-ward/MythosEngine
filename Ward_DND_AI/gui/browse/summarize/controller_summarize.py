import os
import time

from PyQt6.QtCore import QObject

from Ward_DND_AI.utils.crash_handler import catch_and_report_crashes


class SummarizeController(QObject):
    """

    Reads raw notes from the storage, summarizes them via the AI engine,

    displays the result, and then writes the summary into a dedicated

    core_storage folder ("summaries") for later retrieval.

    """

    def __init__(self, view, ctx, status_var=None):
        super().__init__()

        self.view = view

        self.ctx = ctx

        self.ai = ctx.ai

        self.storage = ctx.storage  # Obsidian or file store

        self.config = ctx.config

        self.status_var = status_var or getattr(self.view, "status_label", None)

        # ensure our summaries folder exists in core

        if "summaries" not in self.storage.list_folders():
            self.storage.create_folder("summaries")

        self._load_folders()

        # wire up the button

        self.view.summarize_btn.clicked.connect(catch_and_report_crashes(self.on_summarize))

    def _load_folders(self, *args, **kwargs):
        # list only vault folders for selection

        folders = self.storage.list_folders()

        self.view.folder_menu.clear()

        self.view.folder_menu.addItems(folders)

        if folders:
            self.view.folder_menu.setCurrentIndex(0)

    @catch_and_report_crashes
    def on_summarize(self, *args, **kwargs):
        folder = self.view.folder_menu.currentText().strip()

        style = self.view.style_menu.currentText().strip().lower()

        if not folder:
            self.view.set_output("[No folder selected]")

            if self.status_var:
                self.status_var.setText("❌ No folder selected.")

            return

        notes = self.storage.list_notes(folder)

        if not notes:
            self.view.set_output("[No notes found]")

            if self.status_var:
                self.status_var.setText("⚠️ Folder is empty.")

            return

        # gather contents

        contents = []

        for fn in notes:
            # storage returns paths *relative* to vault root

            text = self.storage.read_note(fn)

            contents.append(text)

        combined = "\n\n".join(contents)

        prompt = f"Summarize the following notes in a {style} format:\n\n{combined[:1000]}..."

        summary_res = self.ai.summarize(prompt)

        # normalize the tuple / string output

        if isinstance(summary_res, tuple):
            summary, p_tokens, r_tokens = summary_res[0], summary_res[1], summary_res[2]

        else:
            summary, p_tokens, r_tokens = str(summary_res), 0, 0

        # display

        self.view.set_output(f"{summary}\n\n[Prompt tokens: {p_tokens} | Response tokens: {r_tokens}]")

        if self.status_var:
            self.status_var.setText(f"✅ Summarized {len(notes)} notes.")

        # save into core_storage under summaries/<folder>_<ts>.md

        ts = time.strftime("%Y%m%d_%H%M%S")

        safe_folder = folder.replace("/", "_")

        filename = f"{safe_folder}_{ts}.md"

        path = os.path.join("summaries", filename)

        try:
            self.storage.write_note(path, summary)

        except Exception as e:
            print(f"[WARN] failed to save summary to vault: {e}")
