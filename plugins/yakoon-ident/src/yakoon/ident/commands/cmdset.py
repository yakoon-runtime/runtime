from yakoon.base.commands import CommandSet

from .cmd_group import CmdGroup
from .cmd_member import CmdMembership
from .cmd_su import CmdSu
from .cmd_user import CmdUser
from .cmd_whoami import CmdWhoAmI


class AuthCommands(CommandSet):

    group = "auth"

    commands = (
        CmdSu,
        CmdWhoAmI,
    )


class AdminCommands(CommandSet):

    group = "users"

    commands = (
        CmdUser,
        CmdGroup,
        CmdMembership,
    )
