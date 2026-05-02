from yakoon.base.commands import CommandSet

from .cmd_test import CmdTest
from .cmd_test_city import CmdTestCity


class TestCommands(CommandSet):

    group = "test"

    commands = (
        CmdTest,
        CmdTestCity,
    )
