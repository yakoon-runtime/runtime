from __future__ import annotations

from typing import Protocol

from yakoon.base.commands import Command, Invocation, Request
from yakoon.base.flow import receive
from yakoon.base.flow.patterns import form
from yakoon.base.plugins.ports import OnProject


class CmdQuit(Command):

    key = "quit"
    anonymous = True

    invocations = [
        Invocation(),
    ]

    def __init__(
        self,
        on_project: OnProject,
        on_set_mark: OnSetMark,
    ):
        self.on_project = on_project
        self.on_set_mark = on_set_mark

    async def run(self, request: Request):

        projection = await self.on_project(
            key="quit:confirm",
            scope="shell",
            lang=request.lang,
        )

        yield form(self, projection, "form")

        result = yield receive("form")

        answer = bool(result.values.get("quit"))
        if answer:
            self.on_set_mark(name="exit_app")


# ----------------------------------
# PORTS
# ----------------------------------


class OnSetMark(Protocol):
    def __call__(self, *, name: str) -> None: ...
