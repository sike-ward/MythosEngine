from PyQt6.QtCore import QObject

from Ward_DND_AI.utils.crash_handler import catch_and_report_crashes


class CampaignSettingsController(QObject):
    def __init__(self, view, ctx):
        super().__init__()

        self.view = view

        self.ctx = ctx

        self.config = ctx.config

        self.storage = ctx.storage

        self.ai_engine = ctx.ai

        self._load_settings()

        self.view.save_clicked.connect(catch_and_report_crashes(self.save_settings))

    def _load_settings(self):
        # Load current config values into UI

        self.view.set_vault_path(self.config.VAULT_PATH or "")

        self.view.set_api_key(self.config.OPENAI_API_KEY or "")

    @catch_and_report_crashes
    def save_settings(self):
        vault_path = self.view.get_vault_path().strip()

        api_key = self.view.get_api_key().strip()

        # Validation

        if not vault_path:
            self.view.set_status("Error: Vault Path cannot be empty.")

            return

        if not api_key:
            self.view.set_status("Error: API Key cannot be empty.")

            return

        vault_changed = vault_path != self.config.VAULT_PATH

        api_key_changed = api_key != self.config.OPENAI_API_KEY

        # Update config

        self.config.VAULT_PATH = vault_path

        self.config.OPENAI_API_KEY = api_key

        self.config.save()

        # Reload storage backend if vault path changed

        if vault_changed:
            try:
                self.storage.reload(vault_path)

                self.view.set_status("Vault path updated and storage reloaded.")

            except Exception as e:
                self.view.set_status(f"Failed to reload storage: {e}")

                return

        else:
            self.view.set_status("Vault path unchanged.")

        # Update AI engine API key live if changed

        if self.ai_engine and api_key_changed:
            try:
                self.ai_engine.update_api_key(api_key)

                self.view.set_status("API key updated and AI engine reconfigured.")

            except Exception as e:
                self.view.set_status(f"Failed to update AI engine API key: {e}")

                return

        elif not api_key_changed:
            self.view.set_status("API key unchanged.")

        # If both changed or unchanged, combine messages sensibly

        if vault_changed and api_key_changed:
            self.view.set_status("Vault and API key updated successfully.")

        # Further hooks for other runtime updates can be added here
