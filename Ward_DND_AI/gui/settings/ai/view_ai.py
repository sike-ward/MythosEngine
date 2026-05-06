from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class AISettingsView(QWidget):
    save_clicked = pyqtSignal()

    def __init__(self, parent, ctx):
        super().__init__(parent)

        self.ctx = ctx

        self.config = ctx.config

        self.ai_engine = ctx.ai

        layout = QVBoxLayout(self)

        layout.setContentsMargins(15, 15, 15, 15)

        layout.setSpacing(10)

        # API Key

        self.label_api_key = QLabel("OpenAI API Key:")

        self.input_api_key = QLineEdit()

        self.input_api_key.setEchoMode(QLineEdit.EchoMode.Password)

        layout.addWidget(self.label_api_key)

        layout.addWidget(self.input_api_key)

        # Embedding Model

        self.label_embedding_model = QLabel("Embedding Model:")

        self.combo_embedding_model = QComboBox()

        self.combo_embedding_model.addItems(
            [
                "text-embedding-3-small",
                "text-embedding-3-large",
                # add more if needed
            ]
        )

        layout.addWidget(self.label_embedding_model)

        layout.addWidget(self.combo_embedding_model)

        # Completion Model

        self.label_completion_model = QLabel("Completion Model:")

        self.combo_completion_model = QComboBox()

        self.combo_completion_model.addItems(
            [
                "gpt-4o",
                "gpt-3.5-turbo",
                # add more if needed
            ]
        )

        layout.addWidget(self.label_completion_model)

        layout.addWidget(self.combo_completion_model)

        # Max Tokens

        self.label_max_tokens = QLabel("Max Tokens:")

        self.input_max_tokens = QLineEdit()

        layout.addWidget(self.label_max_tokens)

        layout.addWidget(self.input_max_tokens)

        # Token Usage Display

        self.label_token_usage = QLabel("Tokens used: 0 / 0")

        layout.addWidget(self.label_token_usage)

        # Save Button

        self.btn_save = QPushButton("Save Settings")

        layout.addWidget(self.btn_save)

        self.btn_save.clicked.connect(self.save_clicked.emit)

    # Convenience methods for controller to get/set values

    def get_api_key(self):
        return self.input_api_key.text()

    def set_api_key(self, key):
        self.input_api_key.setText(key)

    def get_embedding_model(self):
        return self.combo_embedding_model.currentText()

    def set_embedding_model(self, model):
        index = self.combo_embedding_model.findText(model)

        if index >= 0:
            self.combo_embedding_model.setCurrentIndex(index)

    def get_completion_model(self):
        return self.combo_completion_model.currentText()

    def set_completion_model(self, model):
        index = self.combo_completion_model.findText(model)

        if index >= 0:
            self.combo_completion_model.setCurrentIndex(index)

    def get_max_tokens(self):
        try:
            return int(self.input_max_tokens.text())

        except ValueError:
            return 4000  # default fallback

    def set_max_tokens(self, max_tokens):
        self.input_max_tokens.setText(str(max_tokens))

    def set_token_usage(self, used, max_tokens):
        self.label_token_usage.setText(f"Tokens used: {used} / {max_tokens}")
