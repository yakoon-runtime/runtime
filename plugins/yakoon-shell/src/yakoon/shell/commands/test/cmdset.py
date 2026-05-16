from yakoon.base.commands import CommandGroup

from .cmd_test import CmdTest
from .cmd_test_city import CmdTestCity


class TestCommands(CommandGroup):

    group = "test"

    commands = (
        CmdTest,
        CmdTestCity,
    )
