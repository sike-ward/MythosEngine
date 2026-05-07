import webbrowser

from PyQt6.QtCore import QObject

from Ward_DND_AI.gui.settings.help.debug.controller_debug import DebugController
from Ward_DND_AI.utils.crash_handler import catch_and_report_crashes


class HelpController(QObject):
    def __init__(self, view, ctx, status_var=None):
        super().__init__()

        self.v = view

        self.ctx = ctx

        self.ai = ctx.ai

        self.storage = ctx.storage

        self.config = ctx.config

        self.status_var = status_var or ""

        # --- Documentation Tab Wiring ---

        self.v.link_button.clicked.connect(catch_and_report_crashes(self.open_docs))

        self._populate()

        # --- Debug/Log Tab Wiring ---

        self.debug_controller = DebugController(self.v.debug_view, self.ctx)

    @catch_and_report_crashes
    def _populate(self):
        help_text = (
            "Welcome to the Obsidian Lore Assistant!\n\n"
            "• Ask AI Tab: Type your question and click 'Ask'.\n"
            "• Browse Vault Tab: Browse and manage your notes.\n"
            "• Summarize Tab: Summarize notes by folder.\n"
            "• Random Generator Tab: Generate random content.\n"
            "• Timeline Tab: Manage your campaign events.\n"
            "For full documentation, visit: https://github.com/yourrepo/wiki"
        )

        self.v.set_text(help_text)

        self.status_var = "✅ Help loaded."

    @catch_and_report_crashes
    def open_docs(self):
        try:
            webbrowser.open("https://github.com/yourrepo/wiki")

            self.status_var = "📖 Opening documentation in browser..."

        except Exception:
            self.status_var = "❌ Failed to open documentation."
