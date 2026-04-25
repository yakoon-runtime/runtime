from yakoon.base.plugins import ModuleExport, ModuleImport, ModuleMeta

meta = ModuleMeta(
    name="yakoon.crm",
    version="0.1.0",
    description="CRM ...",
)


def register(ports: ModuleImport) -> ModuleExport:

    return ModuleExport(
        meta,
        app=None,
        # controllers=[
        #    CrmCustomerCoreController,
        # ],
    )
