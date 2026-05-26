from y5n.base.capabilities.workflow import WorkflowService
from y5n.base.commands import (
    Command,
    CommandKind,
    CommandScope,
    CommandVisibility,
    Request,
)


class CmdWfRun(Command):

    key = "wf.run"

    kind = CommandKind.WORKFLOW
    scope = CommandScope.GLOBAL
    visibility = CommandVisibility.INTERNAL

    async def run(self, request: Request) -> None:  # noqa: ARG002

        key = request.arg(0)  # "kunden_anlage" oder "shell:kunden_anlage"
        if not self.ctx:
            raise RuntimeError("Context cannot be None.")

        controller_id = self.ctx.controller.id  # kommt aus deinem Dispatcher

        wfsvc = self.container.get(WorkflowService)
        wfsvc.start(session, controller_id, key)
