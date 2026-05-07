from PyQt6.QtCore import QObject


class AppSettingsController(QObject):
    def __init__(self, view, ctx, app):
        super().__init__()

        self.view = view

        self.ctx = ctx

        self.config = ctx.config

        self.app = app

        # --- Connect UI to Logic ---

        self.view.theme_combo.currentTextChanged.connect(self.on_theme_changed)

        self.view.font_size_combo.currentTextChanged.connect(self.on_font_size_changed)

        self.view.compact_mode_checkbox.toggled.connect(self.on_compact_mode_changed)

        self.view.tooltips_checkbox.toggled.connect(self.on_tooltips_changed)

        self.view.startup_tab_combo.currentTextChanged.connect(self.on_startup_tab_changed)

    def on_theme_changed(self, theme):
        self.config.THEME = theme  # auto-saves

        # Apply theme instantly

        if theme == "Dark":
            # Example: very basic dark theme

            qss = """

            QWidget { background-color: #222; color: #eee; }

            QPushButton { background: #333; color: #eee; }

            QLineEdit, QTextEdit { background: #2a2a2a; color: #eee; }

            QComboBox { background: #333; color: #eee; }

            QCheckBox { color: #eee; }

            """

        else:
            qss = ""  # Default system theme (no stylesheet)

        # This will apply the QSS globally dont forget to add custom styles for your widgets

        from PyQt6.QtWidgets import QApplication

        QApplication.instance().setStyleSheet(qss)

    def on_font_size_changed(self, size):
        self.config.FONT_SIZE = size  # auto-saves

        from PyQt6.QtGui import QFont

        font_map = {"Small": 10, "Medium": 12, "Large": 16}

        font_size = font_map.get(size, 12)

        QApplication = __import__("PyQt6.QtWidgets", fromlist=["QApplication"]).QApplication

        QApplication.instance().setFont(QFont("Segoe UI", font_size))

    def on_compact_mode_changed(self, enabled):
        self.config.COMPACT_MODE = enabled

        # Example: Use a QSS to change paddings/margins

        from PyQt6.QtWidgets import QApplication

        if enabled:
            qss = """

            QWidget { padding: 2px; }

            QVBoxLayout, QHBoxLayout { spacing: 2px; }

            """

            QApplication.instance().setStyleSheet(QApplication.instance().styleSheet() + qss)

        else:
            # Re-apply current theme only

            self.on_theme_changed(self.config.THEME)

    def on_tooltips_changed(self, enabled):
        self.config.SHOW_TOOLTIPS = enabled

        # Hide/show all tooltips. Easiest way is to monkeypatch QToolTip.showText

        from PyQt6.QtWidgets import QToolTip

        if not enabled:
            QToolTip.showText = lambda *a, **k: None  # disables all

        else:
            # Reset by reloading module (advanced) or do nothing (Qt will use defaults)

            import importlib

            importlib.reload(__import__("PyQt6.QtWidgets.QToolTip", fromlist=["QToolTip"]))

    def on_startup_tab_changed(self, tab):
        self.config.STARTUP_TAB = tab
