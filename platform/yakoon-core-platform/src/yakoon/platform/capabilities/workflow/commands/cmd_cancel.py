from yakoon.base.capabilities.interaction import DialogService
from yakoon.base.capabilities.workflow import WorkflowService
from yakoon.base.engine import CommandQueueService
from yakoon.base.runtime import (
    Command,
    CommandKind,
    CommandScope,
    CommandVisibility,
    Request,
    Session,
)
from yakoon.base.ui import v_error


class CmdWfCancel(Command):

    key = "wf.cancel"

    kind = CommandKind.WORKFLOW
    scope = CommandScope.GLOBAL
    visibility = CommandVisibility.INTERNAL
    requires_workflow = True

    async def run(self, session: Session, request: Request) -> None:

        wfsvc = self.services.get(WorkflowService)
        queue = self.services.get(CommandQueueService)

        rt = wfsvc.runtime(session)
        if not self.context:
            raise RuntimeError("Context cannot be None.")

        batch_id = self.context.batch_id
        batch = rt.get(batch_id or "")
        if not batch:
            await session.emit(v_error("Kein aktiver Workflow."))
            return

        # 1) Queue abbrechen
        queue.cancel_batch(session, batch.batch_id)

        # 2) Runtime aufräumen
        rt.remove(batch.batch_id)

        # 3) Dialog ggf. schließen
        dialogs = self.services.get(DialogService)
        if dialogs.is_waiting(session):
            dialogs.cancel_input(session)

        # 4) Feedback (optional)
        await session.emit(v_error("Workflow abort."))
