from __future__ import annotations

from y5n.base.controllers import Composer

from ..commands.cmdset import JobsCommands


class JobsComposer(Composer):

    command_groups = (JobsCommands,)
