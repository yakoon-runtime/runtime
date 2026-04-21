from yakoon.base.commands import CommandSet

from .cmd_jobs import CmdJobs


class JobsCommands(CommandSet):

    group = "jobs"

    commands = (CmdJobs,)
