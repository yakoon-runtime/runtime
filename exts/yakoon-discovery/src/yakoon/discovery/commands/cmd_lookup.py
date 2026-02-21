from __future__ import annotations

from yakoon.base.commands.command import Command
from yakoon.base.commands.request import Request
from yakoon.base.models.command import CommandScope, CommandVisibility
from yakoon.base.runtime.session import Session
from yakoon.discovery import ports


class CmdLookup(Command):

    key = "lookup"
    scope = CommandScope.GLOBAL
    visibility = CommandVisibility.INTERNAL

    async def run(self, session: Session, request: Request) -> None:

        presenter = await self.get_presenter(session)
        store = self.services.get(ports.LookupCandidateStoreService)

        token = request.option("token")
        if not token:
            await presenter.views.emit("not_found", query=request.raw)
            return

        payload = store.get(token)
        if not payload:
            await presenter.views.emit("not_found", query=request.raw)
            return

        await presenter.views.emit(
            "choose",
            query=payload.query,
            candidates=list(payload.candidates),
        )

        store.delete(token)
