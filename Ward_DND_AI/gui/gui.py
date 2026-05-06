import sys

from PyQt6.QtWidgets import (
    QMainWindow,
    QMenu,
    QMenuBar,
    QStatusBar,
    QTabWidget,
)

# Browse tab
from Ward_DND_AI.gui.browse.controller_browse import BrowseController
from Ward_DND_AI.gui.browse.view_browse import BrowseView

# Ask AI tab
from Ward_DND_AI.gui.chat.controller_chat import ChatController
from Ward_DND_AI.gui.chat.view_chat import ChatView

# Create tab (Random Generator)
from Ward_DND_AI.gui.create.controller_create import CreateController
from Ward_DND_AI.gui.create.view_create import CreateView

# Dashboard tab
from Ward_DND_AI.gui.dashboard.controller_dashboard import DashboardController
from Ward_DND_AI.gui.dashboard.view_dashboard import DashboardView

# Settings tab
from Ward_DND_AI.gui.settings.controller_settings import SettingsController
from Ward_DND_AI.gui.settings.view_settings import SettingsView

# Universe (Timeline) tab
from Ward_DND_AI.gui.universe.timeline.controller_timeline import TimelineController
from Ward_DND_AI.gui.universe.timeline.view_timeline import TimelineView


class LoreMainApp(QMainWindow):
    def __init__(self, ctx):
        super().__init__()
        self.ctx = ctx
        self.ai = ctx.ai
        self.storage = ctx.storage
        self._config = ctx.config

        self.setWindowTitle(getattr(ctx.config, "APP_NAME", "Ward DND AI"))
        self.resize(1024, 768)

        # --- Central Tab Widget ---
        self.tabview = QTabWidget()
        self.setCentralWidget(self.tabview)
        self.tabs = {}

        # --- Dashboard Tab ---
        dash_view = DashboardView(self.tabview, self._config)
        self.dashboard_controller = DashboardController(dash_view, self.ctx)
        self.tabview.addTab(dash_view, "Dashboard")
        self.tabs["Dashboard"] = dash_view

        # --- AI (Ask) Tab ---
        ai_view = ChatView(self.tabview, self._config)
        self.ask_controller = ChatController(ai_view, self.ctx)
        self.tabview.addTab(ai_view, "AI")
        self.tabs["AI"] = ai_view

        # --- Browse Tab ---
        browse_view = BrowseView(self.tabview, self._config)
        self.browse_controller = BrowseController(browse_view, self.ctx)
        self.tabview.addTab(browse_view, "Browse")
        self.tabs["Browse"] = browse_view

        # --- Create Tab ---
        create_view = CreateView(self.tabview, self._config)
        self.create_controller = CreateController(create_view, self.ctx)
        self.tabview.addTab(create_view, "Create")
        self.tabs["Create"] = create_view

        # --- Universe (Timeline) Tab ---
        universe_view = TimelineView(self.tabview, self._config)
        self.timeline_controller = TimelineController(universe_view, self.ctx)
        self.tabview.addTab(universe_view, "Universe")
        self.tabs["Universe"] = universe_view

        # --- Settings Tab ---
        settings_view = SettingsView(self.tabview, self.ctx)
        self.settings_controller = SettingsController(settings_view, self.ctx)
        self.tabview.addTab(settings_view, "Settings")
        self.tabs["Settings"] = settings_view

        # --- Status Bar ---
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        self.statusbar.showMessage("Ready")

        # --- Menu and Shortcuts ---
        self._setup_menubar()
        self._setup_shortcuts()

    def _setup_menubar(self):
        from PyQt6.QtGui import QAction, QKeySequence

        menubar = QMenuBar(self)
        filemenu = QMenu("File", self)

        # New Note
        new_action = QAction("New Note", self)
        new_action.setShortcut(QKeySequence("Ctrl+N"))
        new_action.triggered.connect(self._menu_new_note)
        filemenu.addAction(new_action)

        # Import Note
        import_action = QAction("Import Note", self)
        import_action.setShortcut(QKeySequence("Ctrl+I"))
        import_action.triggered.connect(self._menu_import_note)
        filemenu.addAction(import_action)

        # Export Note
        export_action = QAction("Export Note", self)
        export_action.setShortcut(QKeySequence("Ctrl+S"))
        export_action.triggered.connect(self._menu_export_note)
        filemenu.addAction(export_action)

        filemenu.addSeparator()

        # Exit
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        filemenu.addAction(exit_action)

        menubar.addMenu(filemenu)
        self.setMenuBar(menubar)

    def _setup_shortcuts(self):
        from PyQt6.QtGui import QKeySequence, QShortcut

        tab_bindings = [
            ("Ctrl+1", "Dashboard"),
            ("Ctrl+2", "AI"),
            ("Ctrl+3", "Browse"),
            ("Ctrl+4", "Create"),
            ("Ctrl+5", "Universe"),
            ("Ctrl+6", "Settings"),
        ]
        for seq, label in tab_bindings:
            sc = QShortcut(QKeySequence(seq), self)
            sc.activated.connect(lambda lbl=label: self.tabview.setCurrentWidget(self.tabs.get(lbl, self.centralWidget())))

    # --- Menu Actions ---
    def _menu_new_note(self):
        self.tabview.setCurrentWidget(self.tabs.get("Browse", self.centralWidget()))
        if hasattr(self, "browse_controller"):
            self.browse_controller.new_note()

    def _menu_import_note(self):
        self.tabview.setCurrentWidget(self.tabs.get("Browse", self.centralWidget()))
        if hasattr(self, "browse_controller"):
            self.browse_controller.import_notes()

    def _menu_export_note(self):
        self.tabview.setCurrentWidget(self.tabs.get("Browse", self.centralWidget()))
        if hasattr(self, "browse_controller"):
            self.browse_controller.export_notes()


# Standalone run for testing window only
if __name__ == "__main__":
    from Ward_DND_AI.utils.crash_handler import ExceptionCatchingApplication

    app = ExceptionCatchingApplication(sys.argv)
    # window = LoreMainApp()  # requires ctx — use main.py for full launch
    # window.show()  # requires ctx
    sys.exit(app.exec())
