from yakoon.base.commands.command import Command, CommandVisibility
from yakoon.base.commands.request import Request
from yakoon.base.models.command import CommandKind, CommandScope
from yakoon.base.runtime.session.session import Session
from yakoon.workflow import ports as wf_ports


class CmdWfRun(Command):

    key = "wf.run"

    kind = CommandKind.WORKFLOW
    scope = CommandScope.GLOBAL
    visibility = CommandVisibility.INTERNAL
    requires_workflow = True

    async def run(self, session: Session, request: Request) -> None:  # noqa: ARG002

        key = request.arg(0)  # "kunden_anlage" oder "shell:kunden_anlage"
        if not self.context:
            raise RuntimeError("Context cannot be None.")

        controller_id = self.context.controller.id  # kommt aus deinem Dispatcher

        wfsvc = self.services.get(wf_ports.WorkflowService)
        wfsvc.start(session, controller_id, key)
