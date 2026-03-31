from typing import Any

from yakoon.base.capabilities.workflow import WorkflowCompiler, WorkflowService
from yakoon.base.plugins import ModuleExport, ModuleMeta
from yakoon.base.runtime import Container

from .controllers import WorkflowController
from .services import DefaultWorkflowCompileService, DefaultWorkflowService

meta = ModuleMeta(
    name="yakoon.workflow",
    version="0.1.0",
    description="Workflow ...",
)


def register(container: Container) -> ModuleExport:

    public_ports: list[type] = []

    # provide: internal module service (not exported to platform)
    def provide(port_type: type[Any], instance: Any) -> None:
        container.register_static(port_type, instance)

    # publish: public capability port exported to the platform
    def publish(port_type: type, instance: object) -> None:
        provide(port_type, instance)
        public_ports.append(port_type)

    provide(WorkflowCompiler, DefaultWorkflowCompileService())

    publish(WorkflowService, DefaultWorkflowService(container))

    return ModuleExport(
        meta,
        controllers=[WorkflowController],
        public_ports=public_ports,
    )
