from __future__ import annotations

from yakoon.base.capabilities.discovery import LookupCandidateStoreService
from yakoon.base.runtime import (
    Command,
    CommandScope,
    CommandVisibility,
    Request,
    Session,
)


class CmdLookup(Command):

    key = "lookup"
    scope = CommandScope.GLOBAL
    visibility = CommandVisibility.INTERNAL

    async def run(self, session: Session, request: Request) -> None:

        presenter = await self.get_presenter(session)
        store = self.services.get(LookupCandidateStoreService)

        token = request.option("token")
        if not token:
            return

        # if not token:
        #    await presenter.views.emit("not_found", query=request.raw)
        #   return

        payload = store.get(token)
        store.delete(token)

        # if not payload:
        #    await presenter.views.emit("not_found", query=request.raw)
        #    return

        if payload:
            await presenter.views.emit(
                "choose",
                query=payload.query,
                candidates=list(payload.candidates),
            )
