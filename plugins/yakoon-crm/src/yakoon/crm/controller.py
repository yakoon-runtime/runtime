from __future__ import annotations

from yakoon.base.controllers import Controller, ResourceReferences
from yakoon.crm.customer.commands.cmdset import CrmCustomerCommands


class CrmCustomerCoreController(Controller):
    """Controller for CRM customer management.

    Provides:
        - Customer-related commands
        - Customer workflows
        - Templates and workflows under yakoon.crm.customer:customer
    """

    id: str = "crm-customer"

    commandsets = (CrmCustomerCommands,)

    resources = ResourceReferences(
        package="yakoon.crm.customer",
    )
