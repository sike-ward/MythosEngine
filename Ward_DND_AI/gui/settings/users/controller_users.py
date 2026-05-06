"""
User Management controller — admin-only, wired to UserManager via AppContext.
"""

import logging

import bcrypt

logger = logging.getLogger(__name__)
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from Ward_DND_AI.gui.settings.users.view_users import CreateUserDialog, UserManagementView


class UserManagementController:
    """Controls the user management admin panel."""

    def __init__(self, view: UserManagementView, ctx):
        self.view = view
        self.ctx = ctx
        self.view.btn_create.clicked.connect(self._on_create)
        self.view.btn_refresh.clicked.connect(self.refresh)
        self.refresh()

    def refresh(self):
        """Reload all users from storage and populate the table."""
        try:
            users = self._load_all_users()
            self.view.table.setRowCount(0)
            for user in users:
                row = self.view.table.rowCount()
                self.view.table.insertRow(row)
                self.view.table.setItem(row, 0, QTableWidgetItem(user.username))
                self.view.table.setItem(row, 1, QTableWidgetItem(user.email))
                self.view.table.setItem(row, 2, QTableWidgetItem(", ".join(user.roles) or "player"))
                self.view.table.setItem(row, 3, QTableWidgetItem("Active" if user.is_active else "Disabled"))
                self.view.table.setCellWidget(row, 4, self._make_actions(user))
            self.view.show_status(f"{len(users)} account(s) loaded.")
        except Exception as exc:
            self.view.show_status(f"Error loading users: {exc}", error=True)

    def _load_all_users(self):
        """Load all users bypassing access filters (admin only)."""
        from Ward_DND_AI.models.user import User

        users = []
        try:
            from sqlalchemy.orm import Session as SASession

            from Ward_DND_AI.storage.sqlite_backend import UserRecord

            with SASession(self.ctx.storage.engine) as session:
                for rec in session.query(UserRecord).all():
                    try:
                        users.append(User.model_validate_json(rec.data))
                    except Exception as exc:
                        logger.warning("_load_all_users: skipping corrupt user record: %s", exc)
        except Exception as exc:
            logger.error("_load_all_users: database query failed: %s", exc)
        return users

    def _make_actions(self, user):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(4)

        btn_pw = QPushButton("Reset PW")
        btn_pw.setFixedHeight(22)
        btn_pw.clicked.connect(lambda _checked, u=user: self._on_reset_password(u))

        btn_toggle = QPushButton("Disable" if user.is_active else "Enable")
        btn_toggle.setFixedHeight(22)
        if user.is_active:
            btn_toggle.setStyleSheet("color: #e74c3c;")
        btn_toggle.clicked.connect(lambda _checked, u=user: self._on_toggle(u))

        layout.addWidget(btn_pw)
        layout.addWidget(btn_toggle)
        return widget

    def _on_create(self):
        dialog = CreateUserDialog(self.view)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        try:
            if self.ctx.users.get_user_by_email(dialog.email):
                self.view.show_status(f"Email {dialog.email!r} already in use.", error=True)
                return
            self.ctx.users.create_user(
                email=dialog.email,
                username=dialog.username,
                password=dialog.password,
                roles=[dialog.role],
            )
            self.view.show_status(f"Account created: {dialog.username} ({dialog.email})")
            self.refresh()
        except Exception as exc:
            self.view.show_status(f"Failed: {exc}", error=True)

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
                self.ctx.users.update_user(user)
                self.view.show_status(f"Account {'enabled' if user.is_active else 'disabled'}: {user.username}")
                self.refresh()
            except Exception as exc:
                self.view.show_status(f"Error: {exc}", error=True)

    def _on_reset_password(self, user):
        dlg = QDialog(self.view)
        dlg.setWindowTitle(f"Reset Password — {user.username}")
        dlg.setMinimumWidth(320)
        layout = QVBoxLayout(dlg)
        form = QFormLayout()
        pw_input = QLineEdit()
        pw_input.setEchoMode(QLineEdit.EchoMode.Password)
        pw_input.setPlaceholderText("New password (min 8 chars)")
        form.addRow("New password:", pw_input)
        layout.addLayout(form)
        err = QLabel("")
        err.setStyleSheet("color: #e74c3c;")
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
                self.view.show_status(f"Password reset for {user.username}")
            except Exception as exc:
                self.view.show_status(f"Error: {exc}", error=True)
