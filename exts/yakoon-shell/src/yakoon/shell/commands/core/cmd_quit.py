from typing import Protocol, cast

from yakoon.base.commands import Command, Request
from yakoon.base.flow import apply_errors, ask, validate
from yakoon.base.flow.dsl import ValidationResult
from yakoon.base.runtime.input import InputEvent


class _SessionMarkAccess(Protocol):
    def mark(self, name: str): ...


class CmdQuit(Command):

    key = "quit"

    async def run(self, request: Request):

        presenter = await self.get_presenter()
        view = await presenter.render("really_quit")

        while True:
            event: InputEvent = yield ask(view)
            result: ValidationResult = validate(view, event, self.services)
            if not result.ok:
                view = apply_errors(view, result.errors)
                continue
            break

        answer = bool(result.values.get("quit"))
        if answer:
            access = cast(_SessionMarkAccess, self.ctx.session)
            access.mark("exit_app")
