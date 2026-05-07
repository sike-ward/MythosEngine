"""
Admin Panel controller — wires all three tabs to their managers.

Only functional when logged in as an admin; shows an access-denied message
otherwise.
"""

import logging

import bcrypt
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from MythosEngine.gui.settings.users.view_users import (
    CreateUserDialog,
    UserManagementView,
)
from MythosEngine.gui.widgets import AvatarCircle, GlowButton, StatusBadge

logger = logging.getLogger(__name__)


class UserManagementController:
    """Controls the Admin Panel — Users, Invite Codes, Active Sessions."""

    def __init__(self, view: UserManagementView, ctx):
        self.view = view
        self.ctx = ctx

        # ── Guard: non-admins see nothing useful ──────────────────────────
        if not ctx.is_admin:
            view.setEnabled(False)
            view.tabs.setToolTip("Admin access required.")
            return

        # ── Users tab ─────────────────────────────────────────────────────
        view.users_tab.btn_create.clicked.connect(self._on_create)
        view.users_tab.btn_refresh.clicked.connect(self._refresh_users)

        # ── Invite Codes tab ──────────────────────────────────────────────
        view.invites_tab.btn_generate.clicked.connect(self._on_generate_invite)
        view.invites_tab.btn_refresh.clicked.connect(self._refresh_invites)

        # ── Active Sessions tab ───────────────────────────────────────────
        view.sessions_tab.btn_refresh.clicked.connect(self._refresh_sessions)

        # ── Initial data load ─────────────────────────────────────────────
        self._refresh_users()
        self._refresh_invites()
        self._refresh_sessions()

    # ======================================================================
    # Users tab
    # ======================================================================

    def _refresh_users(self):
        try:
            users = self._load_all_users()
            tbl = self.view.users_tab.table
            tbl.setRowCount(0)
            for user in users:
                row = tbl.rowCount()
                tbl.insertRow(row)

                # Col 0: Avatar + Username
                name_widget = QWidget()
                name_widget.setStyleSheet("background: transparent;")
                name_layout = QHBoxLayout(name_widget)
                name_layout.setContentsMargins(8, 4, 8, 4)
                name_layout.setSpacing(10)
                avatar = AvatarCircle(user.username, size=32)
                name_label = QLabel(user.username)
                name_label.setStyleSheet("font-weight: 600; font-size: 9.5pt; background: transparent;")
                name_layout.addWidget(avatar)
                name_layout.addWidget(name_label)
                name_layout.addStretch()
                tbl.setCellWidget(row, 0, name_widget)

                # Col 1: Email
                email_item = QTableWidgetItem(user.email)
                tbl.setItem(row, 1, email_item)

                # Col 2: Role badge
                role_name = user.roles[0] if user.roles else "player"
                role_badge = StatusBadge(role_name.upper(), role_name)
                role_container = QWidget()
                role_container.setStyleSheet("background: transparent;")
                role_lay = QHBoxLayout(role_container)
                role_lay.setContentsMargins(8, 0, 8, 0)
                role_lay.addWidget(role_badge)
                role_lay.addStretch()
                tbl.setCellWidget(row, 2, role_container)

                # Col 3: Status badge
                status_key = "active" if user.is_active else "disabled"
                status_text = "Active" if user.is_active else "Disabled"
                status_badge = StatusBadge(status_text, status_key)
                status_container = QWidget()
                status_container.setStyleSheet("background: transparent;")
                status_lay = QHBoxLayout(status_container)
                status_lay.setContentsMargins(8, 0, 8, 0)
                status_lay.addWidget(status_badge)
                status_lay.addStretch()
                tbl.setCellWidget(row, 3, status_container)

                # Col 4: Action buttons
                tbl.setCellWidget(row, 4, self._make_user_actions(user))

            self.view.users_tab.show_status(f"{len(users)} account(s) loaded.")
        except Exception as exc:
            self.view.users_tab.show_status(f"Error loading users: {exc}", error=True)

    # Keep old name for back-compat (controller_settings may call refresh)
    def refresh(self):
        self._refresh_users()

    def _load_all_users(self):
        """Load all users bypassing the access filter (admin-only raw query)."""
        from MythosEngine.models.user import User

        users = []
        try:
            from sqlalchemy.orm import Session as SASession

            from MythosEngine.storage.sqlite_backend import UserRecord

            with SASession(self.ctx.storage.engine) as session:
                for rec in session.query(UserRecord).all():
                    try:
                        users.append(User.model_validate_json(rec.data))
                    except Exception as exc:
                        logger.warning("_load_all_users: skipping corrupt user record: %s", exc)
        except Exception as exc:
            logger.error("_load_all_users: database query failed: %s", exc)
        return users

    def _make_user_actions(self, user):
        widget = QWidget()
        widget.setStyleSheet("background: transparent;")
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)

        btn_role = GlowButton("Role", "secondary")
        btn_role.setFixedHeight(30)
        btn_role.setFixedWidth(72)
        btn_role.clicked.connect(lambda _checked, u=user: self._on_change_role(u))

        btn_pw = GlowButton("Reset PW", "secondary")
        btn_pw.setFixedHeight(30)
        btn_pw.setFixedWidth(84)
        btn_pw.clicked.connect(lambda _checked, u=user: self._on_reset_password(u))

        btn_toggle = GlowButton(
            "Disable" if user.is_active else "Enable",
            "danger" if user.is_active else "success",
        )
        btn_toggle.setFixedHeight(30)
        btn_toggle.setFixedWidth(80)
        btn_toggle.clicked.connect(lambda _checked, u=user: self._on_toggle(u))

        layout.addWidget(btn_role)
        layout.addWidget(btn_pw)
        layout.addWidget(btn_toggle)
        layout.addStretch()
        return widget

    def _on_create(self):
        dialog = CreateUserDialog(self.view)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        try:
            if self.ctx.users.get_user_by_email(dialog.email):
                self.view.users_tab.show_status(f"Email {dialog.email!r} already in use.", error=True)
                return
            self.ctx.users.create_user(
                email=dialog.email,
                username=dialog.username,
                password=dialog.password,
                roles=[dialog.role],
            )
            self.view.users_tab.show_status(f"Account created: {dialog.username} ({dialog.email})")
            self._refresh_users()
        except Exception as exc:
            self.view.users_tab.show_status(f"Failed: {exc}", error=True)

    def _on_toggle(self, user):
        action = "Disable" if user.is_active else "Enable"
        confirm = QMessageBox.question(
            self.view,
            f"{action} Account",
            f"{action} account for {user.username} ({user.email})?",
        )
        if confirm == QMessageBox.StandardButton.Yes:
            try:
                user.is_active = not user.is_active
                self.ctx.storage.save_user(user)
                # Revoke all sessions if disabling
                if not user.is_active:
                    self.ctx.auth.logout(user.id)
                self.view.users_tab.show_status(
                    f"Account {'enabled' if user.is_active else 'disabled'}: {user.username}"
                )
                self._refresh_users()
                self._refresh_sessions()
            except Exception as exc:
                self.view.users_tab.show_status(f"Error: {exc}", error=True)

    def _on_change_role(self, user):
        """Show a dialog to change a user's system role (admin / gm / player)."""
        from PyQt6.QtWidgets import QComboBox

        dlg = QDialog(self.view)
        dlg.setWindowTitle(f"Change Role — {user.username}")
        dlg.setMinimumWidth(360)
        layout = QVBoxLayout(dlg)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        layout.addWidget(QLabel(f"Current role: {', '.join(user.roles)}"))

        form = QFormLayout()
        form.setSpacing(12)
        role_combo = QComboBox()
        role_combo.addItems(["player", "gm", "admin"])
        role_combo.setMinimumHeight(36)
        # Pre-select the user's highest current role
        current = user.roles[0] if user.roles else "player"
        idx = role_combo.findText(current)
        if idx >= 0:
            role_combo.setCurrentIndex(idx)
        form.addRow("New role:", role_combo)
        layout.addLayout(form)

        err = QLabel("")
        err.setStyleSheet("color: #EF4444; background: transparent;")
        layout.addWidget(err)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)
        layout.addWidget(btns)

        if dlg.exec() == QDialog.DialogCode.Accepted:
            new_role = role_combo.currentText()
            try:
                user.roles = [new_role]
                self.ctx.storage.save_user(user)
                self.view.users_tab.show_status(f"Role updated for {user.username}: {new_role}")
                self._refresh_users()
            except Exception as exc:
                self.view.users_tab.show_status(f"Error: {exc}", error=True)

    def _on_reset_password(self, user):
        dlg = QDialog(self.view)
        dlg.setWindowTitle(f"Reset Password — {user.username}")
        dlg.setMinimumWidth(360)
        layout = QVBoxLayout(dlg)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        form = QFormLayout()
        form.setSpacing(12)
        pw_input = QLineEdit()
        pw_input.setEchoMode(QLineEdit.EchoMode.Password)
        pw_input.setPlaceholderText("New password (min 8 chars)")
        pw_input.setMinimumHeight(36)
        form.addRow("New password:", pw_input)
        layout.addLayout(form)

        err = QLabel("")
        err.setStyleSheet("color: #EF4444; background: transparent;")
        layout.addWidget(err)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)

        def _accept():
            if len(pw_input.text()) < 8:
                err.setText("Password must be at least 8 characters.")
                return
            dlg.accept()

        btns.accepted.connect(_accept)
        btns.rejected.connect(dlg.reject)
        layout.addWidget(btns)

        if dlg.exec() == QDialog.DialogCode.Accepted:
            try:
                new_hash = bcrypt.hashpw(pw_input.text().encode(), bcrypt.gensalt()).decode()
                user.password_hash = new_hash
                self.ctx.storage.save_user(user)
                self.view.users_tab.show_status(f"Password reset for {user.username}")
            except Exception as exc:
                self.view.users_tab.show_status(f"Error: {exc}", error=True)

    # ======================================================================
    # Invite Codes tab
    # ======================================================================

    def _refresh_invites(self):
        try:
            invites = self.ctx.invites.list_all()
            tbl = self.view.invites_tab.table
            tbl.setRowCount(0)
            for inv in invites:
                row = tbl.rowCount()
                tbl.insertRow(row)
                tbl.setItem(row, 0, QTableWidgetItem(inv.code))
                # Resolve creator name
                creator = self.ctx.users.get_user(inv.created_by)
                tbl.setItem(row, 1, QTableWidgetItem(creator.username if creator else inv.created_by[:8]))
                tbl.setItem(row, 2, QTableWidgetItem(inv.created_at.strftime("%b %d")))
                tbl.setItem(row, 3, QTableWidgetItem(inv.expires_at.strftime("%b %d")))

                # Col 4: Status badge or action buttons
                if inv.status == "Active":
                    tbl.setCellWidget(row, 4, self._make_invite_actions(inv))
                else:
                    badge_key = inv.status.lower()
                    badge = StatusBadge(inv.status, badge_key)
                    container = QWidget()
                    container.setStyleSheet("background: transparent;")
                    lay = QHBoxLayout(container)
                    lay.setContentsMargins(8, 0, 8, 0)
                    lay.addWidget(badge)
                    lay.addStretch()
                    tbl.setCellWidget(row, 4, container)

            self.view.invites_tab.show_status(f"{len(invites)} invite(s) loaded.")
        except Exception as exc:
            self.view.invites_tab.show_status(f"Error: {exc}", error=True)

    def _make_invite_actions(self, invite):
        widget = QWidget()
        widget.setStyleSheet("background: transparent;")
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)

        btn_copy = GlowButton("Copy", "secondary")
        btn_copy.setFixedHeight(30)
        btn_copy.setFixedWidth(68)
        btn_copy.clicked.connect(lambda _checked, code=invite.code: self._copy_code(code))

        btn_revoke = GlowButton("Revoke", "danger")
        btn_revoke.setFixedHeight(30)
        btn_revoke.setFixedWidth(76)
        btn_revoke.clicked.connect(lambda _checked, inv=invite: self._on_revoke_invite(inv))

        layout.addWidget(btn_copy)
        layout.addWidget(btn_revoke)
        layout.addStretch()
        return widget

    def _copy_code(self, code: str):
        QApplication.clipboard().setText(code)
        self.view.invites_tab.show_status(f"Copied to clipboard: {code}")

    def _on_generate_invite(self):
        try:
            invite = self.ctx.invites.generate(self.ctx.current_user_id)
            QApplication.clipboard().setText(invite.code)
            QMessageBox.information(
                self.view,
                "New Invite Code Generated",
                f"Code:  {invite.code}\n\n"
                f"Share this code with the person you want to invite.\n"
                f"It expires in 7 days and can only be used once.\n\n"
                f"(The code has been copied to your clipboard.)",
            )
            self._refresh_invites()
        except Exception as exc:
            self.view.invites_tab.show_status(f"Failed to generate code: {exc}", error=True)

    def _on_revoke_invite(self, invite):
        confirm = QMessageBox.question(
            self.view,
            "Revoke Invite Code",
            f"Revoke code {invite.code}? It will no longer be usable.",
        )
        if confirm == QMessageBox.StandardButton.Yes:
            try:
                self.ctx.invites.revoke(invite.id)
                self.view.invites_tab.show_status(f"Revoked: {invite.code}")
                self._refresh_invites()
            except Exception as exc:
                self.view.invites_tab.show_status(f"Error: {exc}", error=True)

    # ======================================================================
    # Active Sessions tab
    # ======================================================================

    def _refresh_sessions(self):
        try:
            sessions = self.ctx.auth._sessions.list_active()
            tbl = self.view.sessions_tab.table
            tbl.setRowCount(0)
            for s in sessions:
                row = tbl.rowCount()
                tbl.insertRow(row)

                # Col 0: Avatar + username
                user = self.ctx.users.get_user(s.owner_id)
                display = user.username if user else s.owner_id[:12]
                name_widget = QWidget()
                name_widget.setStyleSheet("background: transparent;")
                name_layout = QHBoxLayout(name_widget)
                name_layout.setContentsMargins(8, 4, 8, 4)
                name_layout.setSpacing(10)
                avatar = AvatarCircle(display, size=28)
                name_label = QLabel(display)
                name_label.setStyleSheet("font-weight: 600; font-size: 9.5pt; background: transparent;")
                name_layout.addWidget(avatar)
                name_layout.addWidget(name_label)
                name_layout.addStretch()
                tbl.setCellWidget(row, 0, name_widget)

                tbl.setItem(row, 1, QTableWidgetItem(s.created_at.strftime("%b %d %H:%M")))
                tbl.setItem(row, 2, QTableWidgetItem(s.expires_at.strftime("%b %d %H:%M")))
                tbl.setCellWidget(row, 3, self._make_session_actions(s))
            self.view.sessions_tab.show_status(f"{len(sessions)} active session(s).")
        except Exception as exc:
            self.view.sessions_tab.show_status(f"Error: {exc}", error=True)

    def _make_session_actions(self, session):
        widget = QWidget()
        widget.setStyleSheet("background: transparent;")
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)

        btn = GlowButton("Revoke", "danger")
        btn.setFixedHeight(30)
        btn.setFixedWidth(76)
        btn.clicked.connect(lambda _checked, s=session: self._on_revoke_session(s))
        layout.addWidget(btn)
        layout.addStretch()
        return widget

    def _on_revoke_session(self, session):
        try:
            self.ctx.auth._sessions.revoke(session.id)
            self.view.sessions_tab.show_status("Session revoked.")
            self._refresh_sessions()
        except Exception as exc:
            self.view.sessions_tab.show_status(f"Error: {exc}", error=True)
