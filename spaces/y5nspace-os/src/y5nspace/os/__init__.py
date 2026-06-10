from y5n.api.modules import ModuleExport, ModuleMeta

from .space import os


def register() -> ModuleExport:
    return ModuleExport(
        node=os,
        meta=ModuleMeta(
            name="y5n.os",
            version="0.1.0",
            description="OS domain — translate natural language to shell commands",
        ),
    )
