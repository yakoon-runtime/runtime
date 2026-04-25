from __future__ import annotations

from yakoon.base.controllers.controller import Controller

from ..commands.cmdset import JobsCommands


class JobsController(Controller):

    id: str = "jobs"

    commandsets = (JobsCommands,)
