from typing import Any

from yakoon.base.plugins import ModuleExport, ModuleMeta
from yakoon.base.runtime import Container

from .controllers import JobsController

meta = ModuleMeta(
    name="yakoon.jobs",
    version="0.1.0",
    description="jobs ...",
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

    return ModuleExport(
        meta,
        controllers=[JobsController],
        public_ports=public_ports,
    )
