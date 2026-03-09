from typing import Any

from yakoon.base.capabilities.interaction import (
    DialogService,
    InteractionService,
    PolicyService,
)
from yakoon.base.plugins import ModuleExport, ModuleMeta
from yakoon.base.runtime.services import ServiceDirectory

from . import DefaultDialogService, DefaultInteractionService, DefaultPolicyService

meta = ModuleMeta(
    name="yakoon.interaction",
    version="0.1.0",
    description="Interaction...",
)


def register(services: ServiceDirectory) -> ModuleExport:

    public_services: list[type] = []

    # provide: internal module service (not exported to platform)
    def provide(port_type: type[Any], instance: Any) -> None:
        services.register_static(port_type, instance)

    # publish: public capability port exported to the platform
    def publish(port_type: type, instance: object) -> None:
        provide(port_type, instance)
        public_services.append(port_type)

    publish(PolicyService, DefaultPolicyService())
    publish(DialogService, DefaultDialogService())
    publish(InteractionService, DefaultInteractionService(services))

    return ModuleExport(
        meta,
        controllers=[],
        public_services=public_services,
    )
