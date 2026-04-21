from yakoon.base.commands import CommandSet
from yakoon.crm.customer.commands.cmd_create import CmdCustomerCreate
from yakoon.crm.customer.commands.cmd_store import CmdCustomerStore
from yakoon.crm.customer.commands.cmd_validate import CmdCustomerValidate


class CrmCustomerCommands(CommandSet):

    group = "customer"

    commands = (
        CmdCustomerCreate,
        CmdCustomerStore,
        CmdCustomerValidate,
    )
