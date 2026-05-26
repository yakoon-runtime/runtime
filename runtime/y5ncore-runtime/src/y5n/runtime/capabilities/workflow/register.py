from y5n.base.plugins import ModuleExport, ModuleMeta

meta = ModuleMeta(
    name="y5n.workflow",
    version="0.1.0",
    description="Workflow ...",
)


def register() -> ModuleExport:

    # provide(WorkflowCompiler, DefaultWorkflowCompileService())
    # publish(WorkflowService, DefaultWorkflowService(container))

    return ModuleExport(
        meta,
        # controllers=[WorkflowController],
    )
