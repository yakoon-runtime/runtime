from collections.abc import Sequence

from yakoon.base.runtime import Command, CommandSet

from .cmd_lookup import CmdLookup


class DiscoveryLookupCommands(CommandSet):

    group = "lookup"

    @classmethod
    def commands(cls) -> Sequence[type[Command]]:
        return [
            CmdLookup,
        ]
