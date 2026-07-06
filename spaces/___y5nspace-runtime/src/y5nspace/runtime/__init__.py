from y5n.api.modules import ModuleExport, ModuleMeta

from .space import runtime


def register() -> ModuleExport:

    return ModuleExport(
        node=runtime,
        meta=ModuleMeta(
            name="y5n.runtime",
            version="0.1.0",
            description="Runtime ...",
        ),
    )
