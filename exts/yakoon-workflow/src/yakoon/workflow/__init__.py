from yakoon.base import ports as base_ports
from yakoon.base.plugins.plugin import PluginExport, PluginMeta
from yakoon.base.runtime.services import ServiceDirectory
from yakoon.workflow import ports as wf_ports
from yakoon.workflow.controller import WorkflowController
from yakoon.workflow.services.compile import WorkflowCompileService
from yakoon.workflow.services.engine import WorkflowService

meta = PluginMeta(
    name="yakoon.workflow",
    version="0.1.0",
    description="Workflow ...",
)


def register(services: ServiceDirectory) -> PluginExport:

    services.register_static(wf_ports.WorkflowService, WorkflowService(services))
    services.register_static(wf_ports.WorkflowCompileService, WorkflowCompileService())

    # register under internal and public access for engine and commands.
    services.register_static(
        base_ports.WorkflowInternal, services.get(wf_ports.WorkflowService)
    )
    services.register_static(
        base_ports.WorkflowPublic, services.get(wf_ports.WorkflowService)
    )

    return PluginExport(
        meta,
        controllers=[
            WorkflowController,
        ],
        public_services=[base_ports.WorkflowInternal, base_ports.WorkflowPublic],
    )
