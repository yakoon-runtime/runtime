from collections.abc import Sequence

from yakoon.base.commands.command import Command
from yakoon.base.commands.commandset import CommandSet
from yakoon.discovery.commands.cmd_lookup import CmdLookup


class DiscoveryLookupCommands(CommandSet):

    group = "lookup"

    @classmethod
    def commands(cls) -> Sequence[type[Command]]:
        return [
            CmdLookup,
        ]
