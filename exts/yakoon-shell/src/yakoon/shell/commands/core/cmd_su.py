from yakoon.base import ports
from yakoon.base.commands.command import Command
from yakoon.base.commands.request import Request
from yakoon.base.runtime.session import Session


class CmdSu(Command):

    key = "su"

    async def run(self, session: Session, request: Request) -> None:  # noqa: ARG002
        wf = self.services.get(ports.WorkflowPublic)  # TODO:
        if not self.context:
            raise RuntimeError("Cannot cannot be None.")

        controller_id = self.context.controller.id
        batch_id = wf.start(
            session, controller_id, command_key=self.key, enqueue_first=False
        )

        wf.set_value(session, batch_id, "user.name", request.arg(0))
        wf.set_value(session, batch_id, "user.password", request.arg(1))

        wf.enqueue_next(session, batch_id)
