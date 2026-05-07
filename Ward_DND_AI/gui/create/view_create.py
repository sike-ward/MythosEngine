from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QTabWidget, QVBoxLayout, QWidget

from Ward_DND_AI.gui.create.random_generator.view_random_generator import (
    RandomGeneratorView,
)


def _make_placeholder(title: str, desc: str) -> QWidget:
    w = QWidget()
    layout = QVBoxLayout(w)
    layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
    lbl_title = QLabel(title)
    lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
    lbl_title.setStyleSheet("font-size: 14pt; font-weight: bold;")
    lbl_desc = QLabel(desc)
    lbl_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
    lbl_desc.setWordWrap(True)
    lbl_coming = QLabel("COMING SOON")
    lbl_coming.setAlignment(Qt.AlignmentFlag.AlignCenter)
    lbl_coming.setStyleSheet("color: #888; font-size: 9pt;")
    layout.addStretch()
    layout.addWidget(lbl_title)
    layout.addSpacing(8)
    layout.addWidget(lbl_desc)
    layout.addSpacing(4)
    layout.addWidget(lbl_coming)
    layout.addStretch()
    return w


class CreateView(QWidget):
    def __init__(self, parent, config):
        super().__init__(parent)
        self.config = config

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        self.subtabs = QTabWidget()

        self.random_view = RandomGeneratorView(self.subtabs, config)
        self.subtabs.addTab(self.random_view, "Random Gen")

        self.subtabs.addTab(
            _make_placeholder("Map Maker", "Draw and annotate campaign maps, pin locations,\nand link places to your lore notes."),
            "Map Maker",
        )
        self.subtabs.addTab(
            _make_placeholder("NPC Builder", "Generate detailed non-player characters with AI,\ncomplete with backstory, traits, and stat blocks."),
            "NPC Builder",
        )
        self.subtabs.addTab(
            _make_placeholder("Quest Designer", "Design quests, side-missions, and encounter hooks\nwith branching outcomes and reward tables."),
            "Quest Designer",
        )

        layout.addWidget(self.subtabs)
