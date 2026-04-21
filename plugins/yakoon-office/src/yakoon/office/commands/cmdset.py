from yakoon.base.commands import CommandSet
from yakoon.office.commands.cmd_sendmail import CmdSendMail


class MailingCommands(CommandSet):

    group = "system"

    commands = (CmdSendMail,)
