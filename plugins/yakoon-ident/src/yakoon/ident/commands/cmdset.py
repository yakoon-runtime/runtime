from yakoon.base.commands import CommandGroup

from .cmd_group import CmdGroup
from .cmd_member import CmdMembership
from .cmd_permgrant import CmdPermissionGrant
from .cmd_su import CmdSu
from .cmd_user import CmdUser
from .cmd_whoami import CmdWhoAmI


class AuthCommands(CommandGroup):

    group = "auth"

    commands = (
        CmdSu,
        CmdWhoAmI,
    )


class AdminCommands(CommandGroup):

    group = "users"

    commands = (
        CmdUser,
        CmdGroup,
        CmdMembership,
        CmdPermissionGrant,
    )
