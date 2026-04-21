from yakoon.base.commands import CommandSet

from .cmd_demo_delay import CmdDemoDelaySimple
from .cmd_demo_focus import CmdDemoFocusSimple
from .cmd_demo_present import CmdDemoPresent
from .cmd_demo_receive import CmdDemoReceiveSimple
from .cmd_demo_send import CmdDemSendSimple


class DemoCommandsDsl(CommandSet):

    group = "dsl"

    commands = (
        CmdDemoDelaySimple,
        CmdDemoFocusSimple,
        CmdDemoPresent,
        CmdDemoReceiveSimple,
        CmdDemSendSimple,
    )
