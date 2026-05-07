from Ward_DND_AI.gui.settings.app.controller_app import AppSettingsController
from Ward_DND_AI.utils.crash_handler import catch_and_report_crashes


class SettingsController:
    def __init__(self, view, ctx):
        self.view = view
        self.ctx = ctx
        self.config = ctx.config
        self.ai_engine = ctx.ai
        self.storage_backend = ctx.storage

        from Ward_DND_AI.gui.settings.ai.controller_ai import AIController
        from Ward_DND_AI.gui.settings.campaign.controller_campaign_settings import (
            CampaignSettingsController,
        )
        from Ward_DND_AI.gui.settings.help.controller_help import HelpController

        self.controllers = {}
        self.controllers["ai"] = AIController(self.view.ai_view, self.ctx)
        self.controllers["campaign"] = CampaignSettingsController(self.view.campaign_view, self.ctx)
        self.controllers["help"] = HelpController(self.view.help_view, self.ctx)

        from Ward_DND_AI.gui.settings.users.controller_users import UserManagementController

        self.controllers["users"] = UserManagementController(self.view.users_view, self.ctx)
        self.controllers["app"] = AppSettingsController(self.view.app_settings_view, self.ctx, None)

        self.view.stacked_widget.addWidget(self.view.ai_view)
        self.view.stacked_widget.addWidget(self.view.campaign_view)
        self.view.stacked_widget.addWidget(self.view.help_view)
        self.view.stacked_widget.insertWidget(0, self.view.app_settings_view)

        self.view.btn_ai.clicked.connect(
            catch_and_report_crashes(lambda checked=False: self.switch_tab("ai"))
        )
        self.view.btn_campaign.clicked.connect(
            catch_and_report_crashes(lambda checked=False: self.switch_tab("campaign"))
        )
        self.view.btn_help.clicked.connect(
            catch_and_report_crashes(lambda checked=False: self.switch_tab("help"))
        )
        self.view.btn_users.clicked.connect(
            catch_and_report_crashes(lambda checked=False: self.switch_tab("users"))
        )
        self.view.btn_app.clicked.connect(
            catch_and_report_crashes(lambda checked=False: self.switch_tab("app"))
        )

        self.switch_tab("ai")
        self._update_button_states("ai")

    def switch_tab(self, tab_name: str) -> None:
        if tab_name == "users":
            self.view.stacked_widget.setCurrentWidget(self.view.users_view)
            self._update_button_states("users")
            return
        if tab_name == "ai":
            self.view.stacked_widget.setCurrentWidget(self.view.ai_view)
        elif tab_name == "campaign":
            self.view.stacked_widget.setCurrentWidget(self.view.campaign_view)
        elif tab_name == "help":
            self.view.stacked_widget.setCurrentWidget(self.view.help_view)
        elif tab_name == "app":
            self.view.stacked_widget.setCurrentWidget(self.view.app_settings_view)
        self._update_button_states(tab_name)

    @catch_and_report_crashes
    def _update_button_states(self, active_tab: str) -> None:
        self.view.btn_ai.setEnabled(active_tab != "ai")
        self.view.btn_campaign.setEnabled(active_tab != "campaign")
        self.view.btn_help.setEnabled(active_tab != "help")
        self.view.btn_app.setEnabled(active_tab != "app")

    def on_config_changed(self, key: str, value) -> None:
        """Propagate a runtime config change to the live AI engine and reload the AI settings view."""
        ai_ctrl = self.controllers.get("ai")
        if key == "OPENAI_API_KEY":
            self.ai_engine.update_api_key(value)
            if ai_ctrl and hasattr(ai_ctrl, "_load_settings"):
                ai_ctrl._load_settings()
        elif key == "COMPLETION_MODEL":
            self.ai_engine.update_models(
                getattr(self.config, "EMBEDDING_MODEL", "text-embedding-3-small"),
                value,
            )
            if ai_ctrl and hasattr(ai_ctrl, "_load_settings"):
                ai_ctrl._load_settings()
        elif key == "EMBEDDING_MODEL":
            self.ai_engine.update_models(
                value,
                getattr(self.config, "COMPLETION_MODEL", "gpt-4o"),
            )
            if ai_ctrl and hasattr(ai_ctrl, "_load_settings"):
                ai_ctrl._load_settings()
        elif key == "MAX_TOKENS":
            self.ai_engine.update_max_tokens(int(value))
            if ai_ctrl and hasattr(ai_ctrl, "_load_settings"):
                ai_ctrl._load_settings()
