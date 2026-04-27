from yakoon.base.plugins import ModuleExport, ModuleMeta

meta = ModuleMeta(
    name="yakoon.workflow",
    version="0.1.0",
    description="Workflow ...",
)


def register() -> ModuleExport:

    # provide(WorkflowCompiler, DefaultWorkflowCompileService())
    # publish(WorkflowService, DefaultWorkflowService(container))

    return ModuleExport(
        meta,
        app=None,
        # controllers=[WorkflowController],
    )
