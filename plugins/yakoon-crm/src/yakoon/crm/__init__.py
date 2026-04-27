from yakoon.base.plugins import ModuleExport, ModuleMeta

meta = ModuleMeta(
    name="yakoon.crm",
    version="0.1.0",
    description="CRM ...",
)


def register() -> ModuleExport:

    return ModuleExport(
        meta,
        app=None,
        # controllers=[
        #    CrmCustomerCoreController,
        # ],
    )
