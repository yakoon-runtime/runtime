from __future__ import annotations

from yakoon.base.commands import (
    Command,
    CommandScope,
    CommandVisibility,
    Request,
)


class CmdLookup(Command):

    key = "lookup"
    scope = CommandScope.GLOBAL
    visibility = CommandVisibility.INTERNAL

    async def run(self, request: Request):

        projector = await self.create_projector()
        store = self.container.get(LookupCandidateStoreService)

        token = request.option("token")
        if not token:
            return

        # if not token:
        #    await projector.project("not_found", query=request.raw)
        #   return

        payload = store.get(token)
        store.delete(token)

        # if not payload:
        #    await projector.project("not_found", query=request.raw)
        #    return

        if payload:
            await projector.project(
                "choose",
                state={
                    "query": payload.query,
                    "candidates": list(payload.candidates),
                },
            )

        return
