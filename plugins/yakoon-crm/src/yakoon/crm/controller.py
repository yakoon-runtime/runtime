from __future__ import annotations

from yakoon.base.controllers import Composer, ResourceReferences
from yakoon.crm.customer.commands.cmdset import CrmCustomerCommands


class CrmCustomerCoreComposer(Composer):

    command_groups = (CrmCustomerCommands,)

    resources = ResourceReferences(
        package="yakoon.crm.customer",
    )
