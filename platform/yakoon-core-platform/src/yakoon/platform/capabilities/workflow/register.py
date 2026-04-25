from yakoon.base.plugins import ModuleExport, ModuleImport, ModuleMeta

meta = ModuleMeta(
    name="yakoon.workflow",
    version="0.1.0",
    description="Workflow ...",
)


def register(ports: ModuleImport) -> ModuleExport:

    # provide(WorkflowCompiler, DefaultWorkflowCompileService())
    # publish(WorkflowService, DefaultWorkflowService(container))

    return ModuleExport(
        meta,
        app=None,
        # controllers=[WorkflowController],
    )
