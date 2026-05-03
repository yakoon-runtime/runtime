from __future__ import annotations

from typing import Protocol

from yakoon.base.commands import Command, Request
from yakoon.base.commands.ports import OnProjectCmd
from yakoon.base.flow import out


class CmdWhoAmI(Command):

    key = "whoami"

    def __init__(
        self,
        on_project: OnProjectCmd,
        on_get_user: OnGetCurrentUserName,
    ):
        self.on_project = on_project
        self.on_get_user_name = on_get_user

    async def run(self, request: Request):
        username = self.on_get_user_name()
        if username:
            projection = await self.on_project(
                name="show.sam",
                state={
                    "user": username,
                },
            )
        else:
            projection = await self.on_project(name="hint.sam")

        yield out(projection)


# ----------------------------------
# PORTS
# ----------------------------------


class OnGetCurrentUserName(Protocol):
    def __call__(self) -> str | None: ...
