from y5n.base.commands import CommandGroup
from y5n.playground.commands.patterns.cmd_demo_form_select import CmdDemoFormSelect

from .cmd_demo_form_simple import CmdDemoFormSimple
from .cmd_demo_subflow import CmdDemoSubflow
from .cmd_demo_validate import CmdDemoValidateSimple


class DemoCommandsPatterns(CommandGroup):

    group = "patterns"

    commands = (
        CmdDemoSubflow,
        CmdDemoValidateSimple,
        CmdDemoFormSimple,
        CmdDemoFormSelect,
    )
