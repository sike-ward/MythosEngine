#!/usr/bin/env python3
"""
MythosEngine — Application entry point.

Launch order:
  1. Load config and logging
  2. Initialise AppContext (SQLite storage, managers, permissions)
  3. Check for saved session token — auto-login if valid
  4. If no valid session:
       a. First launch (no users) → show Setup Wizard
       b. Returning user → show Login dialog
  5. Wire AI engine
  6. Open main window
"""

import logging
import sys
from pathlib import Path

# Ensure project root is on PYTHONPATH
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from PyQt6.QtWidgets import QApplication

from MythosEngine.ai.core.model_router import get_model_backend
from MythosEngine.auth.login_dialog import LoginDialog
from MythosEngine.auth.setup_wizard import SetupWizard
from MythosEngine.config.config import Config
from MythosEngine.context.app_context import AppContext
from MythosEngine.core.event_bus import get_event_bus
from MythosEngine.gui.gui import LoreMainApp
from MythosEngine.utils.crash_handler import catch_and_report_crashes


@catch_and_report_crashes
def main():
    config = Config()
    config.log_info("Config loaded and logging initialized.")
    config.reload()

    logger = logging.getLogger(__name__)
    logger.info("Launching MythosEngine...")

    vault_path = Path(config.VAULT_PATH).resolve()
    api_key = config.OPENAI_API_KEY

    if not vault_path.exists():
        raise FileNotFoundError(f"Vault path does not exist: {vault_path}")
    if not api_key:
        logger.warning(
            "OPENAI_API_KEY is not set — AI features will be disabled. "
            "Add your key to .env or Settings > AI to enable them."
        )

    # --- Initialise AppContext (storage, managers, auth) ---
    ctx = AppContext(config)

    # --- PyQt must be initialised before any dialog is shown ---
    qapp = QApplication(sys.argv)

    # --- Apply MythosEngine design system (respect saved theme) ---
    from MythosEngine.gui import theme as _theme

    _theme.apply(qapp, getattr(config, "THEME", "Dark"))

    def _do_login() -> None:
        """Run the full login flow and launch (or re-launch) the main window."""
        nonlocal window

        user = None

        # 1. Try auto-login from saved session token
        user = ctx.auth.auto_login()

        # 2. First launch — no users at all → show setup wizard
        if user is None:
            from sqlalchemy.orm import Session as SASession

            from MythosEngine.storage.sqlite_backend import UserRecord

            with SASession(ctx.storage.engine) as db:
                no_users = db.query(UserRecord).count() == 0

            if no_users:
                wizard = SetupWizard(storage=ctx.storage)
                if wizard.exec() != SetupWizard.DialogCode.Accepted:
                    logger.info("Setup cancelled — exiting.")
                    qapp.quit()
                    return
                user = wizard.user
                ctx.auth.start_session(user)
                logger.info("First-launch setup complete: %s", user.username)

        # 3. Returning user — show login dialog
        if user is None:
            login = LoginDialog(
                storage=ctx.storage,
                invite_mgr=ctx.invites,
                user_mgr=ctx.users,
            )
            if login.exec() != LoginDialog.DialogCode.Accepted:
                logger.info("Login cancelled — exiting.")
                qapp.quit()
                return
            user = login.user
            ctx.auth.start_session(user)

        # --- Set user context on storage + AppContext ---
        ctx.current_user_id = user.id
        _is_admin = "admin" in user.roles
        _is_gm = "gm" in user.roles
        ctx.storage.set_user_context(user.id, is_admin=_is_admin, is_gm=_is_gm)
        logger.info("Logged in as: %s (%s) admin=%s gm=%s", user.username, user.id, _is_admin, _is_gm)
        get_event_bus().user_logged_in.emit(user.id)

        # --- Re-use or create main window ---
        if window is None:
            # Wire AI engine once (skip if no API key configured)
            if config.OPENAI_API_KEY:
                ai_engine = get_model_backend(config, storage=ctx.storage)
                ctx.ai = ai_engine
            else:
                logger.warning("Skipping AI engine init — no API key configured.")
                ctx.ai = None

            window = LoreMainApp(ctx=ctx)
            # Connect auth.session_ended so logout returns to LoginDialog
            ctx.auth.session_ended.connect(_on_logout)

        window.show()
        logger.info("Application started.")

    def _on_logout() -> None:
        """Called when AuthManager.session_ended fires (logout button)."""
        nonlocal window
        logger.info("Session ended — returning to login dialog.")
        get_event_bus().user_logged_out.emit()
        if window:
            window.hide()
        ctx.current_user_id = None
        _do_login()

    window: LoreMainApp | None = None
    _do_login()

    sys.exit(qapp.exec())


if __name__ == "__main__":
    main()
