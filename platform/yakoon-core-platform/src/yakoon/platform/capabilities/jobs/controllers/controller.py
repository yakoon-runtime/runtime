from __future__ import annotations

from yakoon.base.controllers import Composer

from ..commands.cmdset import JobsCommands


class JobsComposer(Composer):

    command_groups = (JobsCommands,)
