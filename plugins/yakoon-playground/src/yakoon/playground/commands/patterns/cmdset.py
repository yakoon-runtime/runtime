from yakoon.base.commands import CommandSet
from yakoon.playground.commands.patterns.cmd_demo_form_select import CmdDemoFormSelect

from .cmd_demo_form_simple import CmdDemoFormSimple
from .cmd_demo_subflow import CmdDemoSubflow
from .cmd_demo_validate import CmdDemoValidateSimple


class DemoCommandsPatterns(CommandSet):

    group = "patterns"

    commands = (
        CmdDemoSubflow,
        CmdDemoValidateSimple,
        CmdDemoFormSimple,
        CmdDemoFormSelect,
    )
