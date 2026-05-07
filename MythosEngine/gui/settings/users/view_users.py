"""
Admin Panel — tabbed view for administrators.

Tabs:
  0  Users          — create, edit, reset password, enable/disable, delete accounts
  1  Invite Codes   — generate (with expiry picker), copy, revoke, see redemptions
  2  Active Sessions — view details, force-revoke individual or all sessions

Only visible / functional when logged in as an admin.
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QSpinBox,
    QTableWidget,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from MythosEngine.gui.widgets import GlowButton, SectionHeader

# ── Tab indices ────────────────────────────────────────────────────────────────
TAB_USERS = 0
TAB_INVITES = 1
TAB_SESSIONS = 2


def _setup_modern_table(table: QTableWidget, row_height: int = 48):
    """Apply consistent modern styling to a QTableWidget."""
    table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
    table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    table.setShowGrid(False)
    table.setAlternatingRowColors(True)
    table.verticalHeader().setVisible(False)
    table.verticalHeader().setDefaultSectionSize(row_height)
    table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    table.horizontalHeader().setHighlightSections(False)
    table.horizontalHeader().setMinimumHeight(40)


# ── Users tab ─────────────────────────────────────────────────────────────────


class UsersTab(QWidget):
    """User account management table with search, stats, and full CRUD actions."""

    # Columns: Username | Email | Role | Status | Last Login | Actions
    COL_USERNAME = 0
    COL_EMAIL = 1
    COL_ROLE = 2
    COL_STATUS = 3
    COL_LAST_LOGIN = 4
    COL_ACTIONS = 5

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 16, 0, 0)
        layout.setSpacing(10)

        # ── Stats bar ─────────────────────────────────────────────────────
        self.stats_label = QLabel("Loading…")
        self.stats_label.setStyleSheet(
            "color: #9ca3af; font-size: 8.5pt; background: transparent;"
        )
        layout.addWidget(self.stats_label)

        # ── Toolbar ───────────────────────────────────────────────────────
        toolbar = QHBoxLayout()
        toolbar.setSpacing(10)

        self.btn_create = GlowButton("✚  Create Account", "primary")
        self.btn_create.setFixedWidth(175)
        self.btn_create.setMinimumHeight(38)

        self.btn_export = GlowButton("⬇  Export CSV", "secondary")
        self.btn_export.setFixedWidth(120)
        self.btn_export.setMinimumHeight(38)
        self.btn_export.setToolTip("Export user list to a CSV file")

        self.btn_refresh = GlowButton("↻  Refresh", "secondary")
        self.btn_refresh.setFixedWidth(105)
        self.btn_refresh.setMinimumHeight(38)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍  Search by username or email…")
        self.search_input.setMinimumHeight(36)
        self.search_input.setClearButtonEnabled(True)

        toolbar.addWidget(self.btn_create)
        toolbar.addWidget(self.btn_export)
        toolbar.addWidget(self.btn_refresh)
        toolbar.addWidget(self.search_input, 1)
        layout.addLayout(toolbar)

        # ── Table ─────────────────────────────────────────────────────────
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(
            ["Username", "Email", "Role", "Status", "Last Login", "Actions"]
        )
        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(self.COL_USERNAME, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(self.COL_EMAIL, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(self.COL_ROLE, QHeaderView.ResizeMode.Fixed)
        hdr.setSectionResizeMode(self.COL_STATUS, QHeaderView.ResizeMode.Fixed)
        hdr.setSectionResizeMode(self.COL_LAST_LOGIN, QHeaderView.ResizeMode.Fixed)
        hdr.setSectionResizeMode(self.COL_ACTIONS, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(self.COL_ROLE, 90)
        self.table.setColumnWidth(self.COL_STATUS, 90)
        self.table.setColumnWidth(self.COL_LAST_LOGIN, 130)
        self.table.setColumnWidth(self.COL_ACTIONS, 370)
        _setup_modern_table(self.table, row_height=50)
        layout.addWidget(self.table)

        self.status_label = QLabel("")
        self.status_label.setProperty("role", "muted")
        layout.addWidget(self.status_label)

    def show_status(self, msg: str, error: bool = False):
        color = "#EF4444" if error else "#10B981"
        self.status_label.setStyleSheet(
            f"color: {color}; font-size: 9pt; background: transparent;"
        )
        self.status_label.setText(msg)

    def update_stats(self, total: int, active: int, admins: int, gms: int):
        self.stats_label.setText(
            f"👥 {total} total  ·  ✅ {active} active  ·  "
            f"🛡 {admins} admin  ·  ⚔️  {gms} GM"
        )


# ── Invite Codes tab ──────────────────────────────────────────────────────────


class InviteCodesTab(QWidget):
    """Invite code generation and management with redemption tracking."""

    # Columns: Code | Created By | Created | Expires | Used By | Actions
    COL_CODE = 0
    COL_CREATED_BY = 1
    COL_CREATED = 2
    COL_EXPIRES = 3
    COL_USED_BY = 4
    COL_ACTIONS = 5

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 16, 0, 0)
        layout.setSpacing(14)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(10)

        self.btn_generate = GlowButton("✚  Generate New Code", "primary")
        self.btn_generate.setFixedWidth(195)
        self.btn_generate.setMinimumHeight(38)

        self.btn_refresh = GlowButton("↻  Refresh", "secondary")
        self.btn_refresh.setFixedWidth(105)
        self.btn_refresh.setMinimumHeight(38)

        toolbar.addWidget(self.btn_generate)
        toolbar.addWidget(self.btn_refresh)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(
            ["Code", "Created By", "Created", "Expires", "Used By", "Actions"]
        )
        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(self.COL_CODE, QHeaderView.ResizeMode.Fixed)
        hdr.setSectionResizeMode(self.COL_CREATED_BY, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(self.COL_CREATED, QHeaderView.ResizeMode.Fixed)
        hdr.setSectionResizeMode(self.COL_EXPIRES, QHeaderView.ResizeMode.Fixed)
        hdr.setSectionResizeMode(self.COL_USED_BY, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(self.COL_ACTIONS, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(self.COL_CODE, 155)
        self.table.setColumnWidth(self.COL_CREATED, 105)
        self.table.setColumnWidth(self.COL_EXPIRES, 105)
        self.table.setColumnWidth(self.COL_ACTIONS, 150)
        _setup_modern_table(self.table, row_height=48)
        layout.addWidget(self.table)

        self.status_label = QLabel("")
        self.status_label.setProperty("role", "muted")
        layout.addWidget(self.status_label)

    def show_status(self, msg: str, error: bool = False):
        color = "#EF4444" if error else "#10B981"
        self.status_label.setStyleSheet(
            f"color: {color}; font-size: 9pt; background: transparent;"
        )
        self.status_label.setText(msg)


# ── Active Sessions tab ───────────────────────────────────────────────────────


class ActiveSessionsTab(QWidget):
    """Live session viewer with per-row revoke and a one-click Force Logout All."""

    # Columns: User | Email | Started | Expires | Actions
    COL_USER = 0
    COL_EMAIL = 1
    COL_STARTED = 2
    COL_EXPIRES = 3
    COL_ACTIONS = 4

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 16, 0, 0)
        layout.setSpacing(14)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(10)

        self.btn_refresh = GlowButton("↻  Refresh", "secondary")
        self.btn_refresh.setFixedWidth(105)
        self.btn_refresh.setMinimumHeight(38)

        self.btn_force_logout_all = GlowButton("⚠  Force Logout All", "danger")
        self.btn_force_logout_all.setFixedWidth(170)
        self.btn_force_logout_all.setMinimumHeight(38)
        self.btn_force_logout_all.setToolTip(
            "Immediately revoke every active session (including your own)"
        )

        toolbar.addWidget(self.btn_refresh)
        toolbar.addWidget(self.btn_force_logout_all)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(
            ["User", "Email", "Started", "Expires", "Actions"]
        )
        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(self.COL_USER, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(self.COL_EMAIL, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(self.COL_STARTED, QHeaderView.ResizeMode.Fixed)
        hdr.setSectionResizeMode(self.COL_EXPIRES, QHeaderView.ResizeMode.Fixed)
        hdr.setSectionResizeMode(self.COL_ACTIONS, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(self.COL_STARTED, 140)
        self.table.setColumnWidth(self.COL_EXPIRES, 140)
        self.table.setColumnWidth(self.COL_ACTIONS, 120)
        _setup_modern_table(self.table, row_height=48)
        layout.addWidget(self.table)

        self.status_label = QLabel("")
        self.status_label.setProperty("role", "muted")
        layout.addWidget(self.status_label)

    def show_status(self, msg: str, error: bool = False):
        color = "#EF4444" if error else "#10B981"
        self.status_label.setStyleSheet(
            f"color: {color}; font-size: 9pt; background: transparent;"
        )
        self.status_label.setText(msg)


# ── Admin Panel (top-level, wraps all tabs) ───────────────────────────────────


class UserManagementView(QWidget):
    """
    Admin Panel — container with Users / Invite Codes / Active Sessions tabs.

    Named UserManagementView for backward compatibility with
    view_settings.py and controller_settings.py.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(16)

        header = SectionHeader(
            "🛡️  Admin Panel",
            "Manage users, invite codes, and active sessions.",
        )
        layout.addWidget(header)

        self.tabs = QTabWidget()
        self.users_tab = UsersTab(self.tabs)
        self.invites_tab = InviteCodesTab(self.tabs)
        self.sessions_tab = ActiveSessionsTab(self.tabs)

        self.tabs.addTab(self.users_tab, "👥  Users")
        self.tabs.addTab(self.invites_tab, "🎟️  Invite Codes")
        self.tabs.addTab(self.sessions_tab, "🔑  Active Sessions")
        layout.addWidget(self.tabs, 1)

    # ── Back-compat shims ──────────────────────────────────────────────────────

    @property
    def table(self):
        return self.users_tab.table

    @property
    def btn_create(self):
        return self.users_tab.btn_create

    @property
    def btn_refresh(self):
        return self.users_tab.btn_refresh

    def show_status(self, msg: str, error: bool = False):
        self.users_tab.show_status(msg, error=error)


# ── CreateUserDialog ──────────────────────────────────────────────────────────


class CreateUserDialog(QDialog):
    """Dialog for creating a new user account (admin-initiated)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create Account")
        self.setMinimumWidth(420)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        form = QFormLayout()
        form.setSpacing(12)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("user@example.com")
        self.email_input.setMinimumHeight(36)
        form.addRow("Email:", self.email_input)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Display name")
        self.username_input.setMinimumHeight(36)
        form.addRow("Username:", self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Minimum 8 characters")
        self.password_input.setMinimumHeight(36)
        form.addRow("Password:", self.password_input)

        self.role_combo = QComboBox()
        self.role_combo.addItems(["player", "gm", "admin"])
        self.role_combo.setMinimumHeight(36)
        form.addRow("Role:", self.role_combo)

        layout.addLayout(form)

        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #EF4444; background: transparent;")
        self.error_label.setWordWrap(True)
        layout.addWidget(self.error_label)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _validate_and_accept(self):
        if not self.email_input.text().strip() or "@" not in self.email_input.text():
            self.error_label.setText("Please enter a valid email address.")
            return
        if not self.username_input.text().strip():
            self.error_label.setText("Username is required.")
            return
        if len(self.password_input.text()) < 8:
            self.error_label.setText("Password must be at least 8 characters.")
            return
        self.accept()

    @property
    def email(self):
        return self.email_input.text().strip()

    @property
    def username(self):
        return self.username_input.text().strip()

    @property
    def password(self):
        return self.password_input.text()

    @property
    def role(self):
        return self.role_combo.currentText()


# ── EditUserDialog ────────────────────────────────────────────────────────────


class EditUserDialog(QDialog):
    """Dialog for editing an existing user's username and email (admin)."""

    def __init__(self, user, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Edit User — {user.username}")
        self.setMinimumWidth(420)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        form = QFormLayout()
        form.setSpacing(12)

        self.username_input = QLineEdit(user.username)
        self.username_input.setMinimumHeight(36)
        form.addRow("Username:", self.username_input)

        self.email_input = QLineEdit(user.email)
        self.email_input.setMinimumHeight(36)
        form.addRow("Email:", self.email_input)

        layout.addLayout(form)

        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #EF4444; background: transparent;")
        self.error_label.setWordWrap(True)
        layout.addWidget(self.error_label)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _validate_and_accept(self):
        if len(self.username_input.text().strip()) < 3:
            self.error_label.setText("Username must be at least 3 characters.")
            return
        if "@" not in self.email_input.text():
            self.error_label.setText("Please enter a valid email address.")
            return
        self.accept()

    @property
    def username(self):
        return self.username_input.text().strip()

    @property
    def email(self):
        return self.email_input.text().strip()


# ── GenerateInviteDialog ──────────────────────────────────────────────────────


class GenerateInviteDialog(QDialog):
    """Dialog for configuring and generating a new invite code."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Generate Invite Code")
        self.setMinimumWidth(380)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        layout.addWidget(
            QLabel("Configure the new invite code before generating it.")
        )

        form = QFormLayout()
        form.setSpacing(12)

        self.expiry_spin = QSpinBox()
        self.expiry_spin.setRange(1, 90)
        self.expiry_spin.setValue(7)
        self.expiry_spin.setSuffix(" days")
        self.expiry_spin.setMinimumHeight(36)
        form.addRow("Expires in:", self.expiry_spin)

        self.max_uses_spin = QSpinBox()
        self.max_uses_spin.setRange(1, 50)
        self.max_uses_spin.setValue(1)
        self.max_uses_spin.setSuffix(" use(s)")
        self.max_uses_spin.setMinimumHeight(36)
        form.addRow("Max uses:", self.max_uses_spin)

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Generate & Copy")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    @property
    def expiry_days(self) -> int:
        return self.expiry_spin.value()

    @property
    def max_uses(self) -> int:
        return self.max_uses_spin.value()

