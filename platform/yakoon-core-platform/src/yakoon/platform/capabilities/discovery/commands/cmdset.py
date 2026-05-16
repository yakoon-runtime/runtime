from yakoon.base.commands import CommandGroup

from .cmd_lookup import CmdLookup


class DiscoveryLookupCommands(CommandGroup):

    group = "lookup"

    commands = (CmdLookup,)
