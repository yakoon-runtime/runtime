from y5n.base.commands import CommandGroup

from .cmd_jobs import CmdJobs


class JobsCommands(CommandGroup):

    group = "jobs"

    commands = (CmdJobs,)
