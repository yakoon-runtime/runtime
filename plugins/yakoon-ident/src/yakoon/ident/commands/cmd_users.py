from __future__ import annotations

from typing import Protocol

from yakoon.base.commands import Command, Request
from yakoon.base.commands.ports import OnProjectCmd
from yakoon.base.flow import out


class CmdUsers(Command):

    key = "user"
    use_subcommands = True

    def __init__(
        self,
        on_project: OnProjectCmd,
    ):
        self.on_project = on_project

    async def run(self, request: Request):
        return

        projection = await self.on_project(
            name="show.sam",
            state={"user": ""},
        )
        yield out(projection)


# ----------------------------------
# PORTS
# ----------------------------------


class OnGetCurrentUserName(Protocol):
    def __call__(self) -> str | None: ...
