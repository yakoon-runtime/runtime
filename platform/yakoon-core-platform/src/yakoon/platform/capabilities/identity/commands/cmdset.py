from collections.abc import Sequence

from yakoon.base.runtime.commands import Command, CommandSet

from .cmd_su import CmdSu
from .cmd_whoami import CmdWhoAmI


class AuthSystemCommands(CommandSet):

    group = "system"

    @classmethod
    def commands(cls) -> Sequence[type[Command]]:
        return [
            CmdSu,
            CmdWhoAmI,
        ]
