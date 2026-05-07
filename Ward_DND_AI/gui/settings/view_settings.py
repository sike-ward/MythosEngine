from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from Ward_DND_AI.gui.settings.ai.view_ai import AISettingsView
from Ward_DND_AI.gui.settings.app.view_app import AppSettingsView
from Ward_DND_AI.gui.settings.campaign.view_campaign import CampaignSettingsView
from Ward_DND_AI.gui.settings.help.view_help import HelpView
from Ward_DND_AI.gui.settings.users.view_users import UserManagementView


class SettingsView(QWidget):
    def __init__(self, parent, ctx):
        super().__init__(parent)

        self.ai_engine = ctx.ai

        self.ctx = ctx

        self.config = ctx.config

        # Main horizontal layout for sidebar + content

        main_layout = QHBoxLayout(self)

        main_layout.setContentsMargins(0, 0, 0, 0)

        main_layout.setSpacing(0)

        # Sidebar frame with vertical layout for buttons

        self.sidebar = QFrame(self)

        self.sidebar.setFixedWidth(180)

        sidebar_layout = QVBoxLayout(self.sidebar)

        sidebar_layout.setContentsMargins(10, 10, 10, 10)

        sidebar_layout.setSpacing(8)

        # 1. App Settings FIRST

        self.btn_app = QPushButton("App Settings", self.sidebar)

        self.btn_app.setToolTip("General app preferences (theme, UI, etc)")

        self.btn_app.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        sidebar_layout.addWidget(self.btn_app)  # first widget added will be at the top

        # 2. The rest

        self.btn_ai = QPushButton("AI Settings", self.sidebar)

        self.btn_ai.setToolTip("Configure AI backend and tokens")

        sidebar_layout.addWidget(self.btn_ai)

        self.btn_campaign = QPushButton("Campaign Settings", self.sidebar)

        self.btn_campaign.setToolTip("Configure campaign details")

        sidebar_layout.addWidget(self.btn_campaign)

        self.btn_help = QPushButton("Help & About", self.sidebar)

        self.btn_help.setToolTip("Help documentation and credits")

        sidebar_layout.addWidget(self.btn_help)

        self.btn_users = QPushButton("User Management", self.sidebar)
        self.btn_users.setToolTip("Create and manage user accounts (admin only)")
        sidebar_layout.addWidget(self.btn_users)

        sidebar_layout.addStretch(1)  # Push buttons to top

        # (add other tabs after)

        # Style buttons for uniform size

        for btn in (self.btn_ai, self.btn_campaign, self.btn_help):
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

            sidebar_layout.addWidget(btn)

        sidebar_layout.addStretch(1)  # Push buttons to top

        # Content area with stacked widget to hold subviews

        self.stacked_widget = QStackedWidget(self)

        self.stacked_widget.setContentsMargins(0, 0, 0, 0)

        # Instantiate subviews and add to stacked widget

        self.ai_view = AISettingsView(self, self.ctx)

        self.campaign_view = CampaignSettingsView(self, self.config)

        self.help_view = HelpView(self, self.config)

        self.app_settings_view = AppSettingsView(self, self.config)
        self.users_view = UserManagementView(self)

        self.stacked_widget.addWidget(self.ai_view)

        self.stacked_widget.addWidget(self.campaign_view)

        self.stacked_widget.addWidget(self.help_view)

        self.stacked_widget.insertWidget(0, self.app_settings_view)  # Adjust index if you want another order
        self.stacked_widget.addWidget(self.users_view)

        # Add sidebar and content to main layout

        main_layout.addWidget(self.sidebar)

        main_layout.addWidget(self.stacked_widget, 1)

        # Connect sidebar buttons to switch tabs

        self.btn_ai.clicked.connect(lambda: self.switch_tab(0))

        self.btn_campaign.clicked.connect(lambda: self.switch_tab(1))

        self.btn_help.clicked.connect(lambda: self.switch_tab(2))

        self.btn_app.clicked.connect(lambda: self.switch_tab(0))  # Use 0 if App is first, else adjust index

        # Start with AI tab active

        self.switch_tab(0)

    def switch_tab(self, index: int):
        """Switch the visible subview and update button states."""

        self.stacked_widget.setCurrentIndex(index)

        self._update_button_states(index)

    def _update_button_states(self, active_index: int):
        buttons = [self.btn_ai, self.btn_campaign, self.btn_help, self.btn_app]

        for i, btn in enumerate(buttons):
            btn.setEnabled(i != active_index)

    def set_ai_view(self, ai_view: AISettingsView):
        """Set the AI settings view."""

        self.ai_view = ai_view

        self.content_area.layout().addWidget(self.ai_view)

        self.ai_view.show()

        self.campaign_view.hide()

        self.help_view.hide()

        self._update_button_states("ai")

    def set_campaign_view(self, campaign_view: QWidget):
        """Set the campaign settings view."""

        self.campaign_view = campaign_view

        self.content_area.layout().addWidget(self.campaign_view)

        self.campaign_view.show()

        self.ai_view.hide()

        self.help_view.hide()

        self._update_button_states("campaign")

    def set_help_view(self, help_view: QWidget):
        """Set the help/about view."""

        self.help_view = help_view

        self.content_area.layout().addWidget(self.help_view)
