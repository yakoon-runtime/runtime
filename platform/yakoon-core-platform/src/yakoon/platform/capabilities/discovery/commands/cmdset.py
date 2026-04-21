from yakoon.base.commands import CommandSet

from .cmd_lookup import CmdLookup


class DiscoveryLookupCommands(CommandSet):

    group = "lookup"

    commands = (CmdLookup,)
