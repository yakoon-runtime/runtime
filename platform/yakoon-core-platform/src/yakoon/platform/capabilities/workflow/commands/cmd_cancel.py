from yakoon.base.capabilities.workflow import WorkflowService
from yakoon.base.commands import (
    Command,
    CommandKind,
    CommandScope,
    CommandVisibility,
    Request,
)
from yakoon.base.dispatch import CommandQueueService
from yakoon.base.presentation import v_error_system


class CmdWfCancel(Command):

    key = "wf.cancel"

    kind = CommandKind.WORKFLOW
    scope = CommandScope.GLOBAL
    visibility = CommandVisibility.INTERNAL
    requires_workflow = True

    async def run(self, request: Request) -> None:

        wfsvc = self.services.get(WorkflowService)
        queue = self.services.get(CommandQueueService)

        rt = wfsvc.runtime(session)
        if not self.context:
            raise RuntimeError("Context cannot be None.")

        batch_id = self.context.batch_id
        batch = rt.get(batch_id or "")
        if not batch:
            await session.emit(v_error_system("Kein aktiver Workflow."))
            return

        # 1) Queue abbrechen
        queue.cancel_batch(session, batch.batch_id)

        # 2) Runtime aufräumen
        rt.remove(batch.batch_id)

        # 3) Dialog ggf. schließen
        dialogs = self.services.get()
        if dialogs.is_waiting(session):
            dialogs.cancel_input(session)

        # 4) Feedback (optional)
        await session.emit(v_error_system("Workflow abort."))
