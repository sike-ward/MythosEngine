from PyQt6.QtCore import QObject

from Ward_DND_AI.utils.crash_handler import catch_and_report_crashes


class AIController(QObject):
    def __init__(self, view, ctx):
        super().__init__()

        self.view = view

        self.ctx = ctx

        self.config = ctx.config

        self.ai_engine = ctx.ai

        self.storage_backend = ctx.storage

        self._load_settings()

        self.view.save_clicked.connect(catch_and_report_crashes(self.save_settings))

    def _load_settings(self):
        # Load config values into view

        self.view.set_api_key(self.config.OPENAI_API_KEY or "")

        self.view.set_embedding_model(self.config.EMBEDDING_MODEL or "text-embedding-3-small")

        self.view.set_completion_model(self.config.COMPLETION_MODEL or "gpt-4o")

        self.view.set_max_tokens(self.config.MAX_TOKENS or 4000)

    @catch_and_report_crashes
    def save_settings(self):
        # Get values from view

        api_key = self.view.get_api_key()

        embedding_model = self.view.get_embedding_model()

        completion_model = self.view.get_completion_model()

        max_tokens = self.view.get_max_tokens()

        # Validate api_key at least

        if not api_key:
            # Optionally: show warning dialog

            return

        # Save to config (assuming your config class has setters or you assign to _data and then save)

        self.config.OPENAI_API_KEY = api_key

        self.config.EMBEDDING_MODEL = embedding_model

        self.config.COMPLETION_MODEL = completion_model

        self.config.MAX_TOKENS = max_tokens

        self.config.save()  # Or whatever your config uses to persist changes

        # Update AI engine parameters live if possible

        self.ai_engine.update_api_key(api_key)

        self.ai_engine.update_models(embedding_model, completion_model)

        self.ai_engine.update_max_tokens(max_tokens)

        self.view.set_token_usage(0, max_tokens)  # Reset token usage display for example
