from yakoon.base.commands import CommandGroup

from .cmd_jobs import CmdJobs


class JobsCommands(CommandGroup):

    group = "jobs"

    commands = (CmdJobs,)
