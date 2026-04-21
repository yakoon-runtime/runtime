from __future__ import annotations

from yakoon.base.controllers import Controller, ResourceReferences
from yakoon.office.commands.cmdset import MailingCommands


class OfficeMailingCoreController(Controller):
    """Controller for the Office Mailing domain.

    Provides:
        - Mailing-related commands
        - Template root under yakoon.office.mailing:core
    """

    id: str = "office.mailing"

    commandsets = (MailingCommands,)

    resources = ResourceReferences(
        package="yakoon.office.mailing",
    )
