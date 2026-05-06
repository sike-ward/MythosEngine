from PyQt6.QtCore import QObject

from Ward_DND_AI.gui.create.random_generator.controller_random_generator import (
    RandomGeneratorController,
)


class CreateController(QObject):
    def __init__(self, view, ctx, status_var=None):
        super().__init__()

        self.view = view

        self.ctx = ctx

        self.ai_engine = ctx.ai

        self.storage = ctx.storage

        self.config = ctx.config

        self.status_var = status_var

        # Hook up Random Generator inside Create
        self.random_ctrl = RandomGeneratorController(self.view.random_view, ctx)
