from yakoon.base.commands import CommandGroup
from yakoon.office.commands.cmd_sendmail import CmdSendMail


class MailingCommands(CommandGroup):

    group = "system"

    commands = (CmdSendMail,)
