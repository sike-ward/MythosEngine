import pytest
from unittest.mock import MagicMock


class DummyAI:
    def ask(self, prompt):
        return (f"RESULT:{prompt}", 10, 5)


class DummyCtx:
    def __init__(self):
        self.ai = DummyAI()
        self.storage = MagicMock()
        self.config = MagicMock()
        note_mock = MagicMock()
        note_mock.title = "Test Note"
        notes_mock = MagicMock()
        notes_mock.create_note.return_value = note_mock
        self.notes = notes_mock
        self.current_user_id = "test-user"


@pytest.fixture
def qapp():
    from PyQt6.QtWidgets import QApplication
    import sys
    app = QApplication.instance() or QApplication(sys.argv)
    yield app


def test_random_generator_empty_prompt(qapp):
    from MythosEngine.gui.create.random_generator.view_random_generator import RandomGeneratorView
    from MythosEngine.gui.create.random_generator.controller_random_generator import RandomGeneratorController

    view = RandomGeneratorView(None, MagicMock())
    ctx = DummyCtx()
    ctrl = RandomGeneratorController(view, ctx)

    view.prompt_entry.setText("")
    ctrl.on_generate()
    assert "Please enter a prompt" in view.output_text.toPlainText()


def test_random_generator_with_prompt(qapp):
    from MythosEngine.gui.create.random_generator.view_random_generator import RandomGeneratorView
    from MythosEngine.gui.create.random_generator.controller_random_generator import RandomGeneratorController

    view = RandomGeneratorView(None, MagicMock())
    ctx = DummyCtx()
    ctrl = RandomGeneratorController(view, ctx)

    view.prompt_entry.setText("a dragon")
    ctrl.on_generate()
    output = view.output_text.toPlainText()
    assert "RESULT:" in output
    assert "a dragon" in output
