from yakoon.base.commands import CommandSet

from .cmd_su import CmdSu
from .cmd_whoami import CmdWhoAmI


class AuthSystemCommands(CommandSet):

    group = "system"

    commands = (
        CmdSu,
        CmdWhoAmI,
    )
