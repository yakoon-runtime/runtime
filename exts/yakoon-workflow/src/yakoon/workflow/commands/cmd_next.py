from yakoon.base.runtime import Command, CommandVisibility, Request
from yakoon.base.runtime.commands import CommandKind, CommandScope
from yakoon.base.runtime.sessions.session import Session
from yakoon.workflow import ports as wf_ports


class CmdWfNext(Command):

    key = "wf.next"

    kind = CommandKind.WORKFLOW
    scope = CommandScope.GLOBAL
    visibility = CommandVisibility.INTERNAL
    requires_workflow = True

    async def run(self, session: Session, request: Request) -> None:  # noqa: ARG002

        batch_id = request.arg(0)
        step_id = request.arg(1)

        wfsvc = self.services.get(wf_ports.WorkflowService)
        wfsvc.set_value(session, batch_id, "batch_id", batch_id)
        wfsvc.complete_run_step(session, batch_id=batch_id, step_id=step_id)
