from __future__ import annotations

from yakoon.base.controllers import Composer, ResourceReferences
from yakoon.office.commands.cmdset import MailingCommands


class OfficeMailingCoreComposer(Composer):

    command_groups = (MailingCommands,)

    resources = ResourceReferences(
        package="yakoon.office.mailing",
    )
