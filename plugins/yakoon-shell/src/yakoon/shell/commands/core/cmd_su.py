from yakoon.base.commands import Command, Request


class CmdSu(Command):

    key = "su"

    async def run(self, request: Request):
        wf = self.container.get(WorkflowService)  # TODO:
        if not self.ctx:
            raise RuntimeError("Cannot cannot be None")

        controller_id = self.ctx.controller.id
        batch_id = wf.start(
            session, controller_id, command_key=self.key, enqueue_first=False
        )

        wf.set_value(session, batch_id, "user.name", request.arg(0))
        wf.set_value(session, batch_id, "user.password", request.arg(1))

        wf.enqueue_next(session, batch_id)
