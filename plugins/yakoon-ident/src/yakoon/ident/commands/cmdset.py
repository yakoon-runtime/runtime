from yakoon.base.commands import CommandSet

from .cmd_su import CmdSu
from .cmd_users import CmdUsers
from .cmd_whoami import CmdWhoAmI


class AuthCommands(CommandSet):

    group = "auth"

    commands = (
        CmdSu,
        CmdWhoAmI,
    )


class UserCommands(CommandSet):

    group = "users"

    commands = (CmdUsers,)
