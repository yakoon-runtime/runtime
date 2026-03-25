from collections.abc import Sequence

from yakoon.base.api import Command, CommandSet

from .cmd_jobs import CmdJobs


class JobsCommands(CommandSet):

    group = "jobs"

    @classmethod
    def commands(cls) -> Sequence[type[Command]]:
        return [
            CmdJobs,
        ]
