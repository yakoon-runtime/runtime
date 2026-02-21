from __future__ import annotations

from yakoon.base import ports as base_ports
from yakoon.base.commands.command import Command
from yakoon.base.commands.request import Request
from yakoon.base.models.command import CommandScope, CommandVisibility
from yakoon.base.runtime.session import Session
from yakoon.discovery import ports
from yakoon.discovery.models.discovery import Candidates, Resolved


class CmdLookup(Command):

    key = "lookup"
    scope = CommandScope.GLOBAL
    visibility = CommandVisibility.INTERNAL

    async def run(self, session: Session, request: Request) -> None:

        presenter = await self.get_presenter(session)

        discovery = self.services.get(ports.DiscoveryService)
        queue = self.services.get(base_ports.CommandQueueService)

        query = request.raw

        result = await discovery.discover(session, request)

        # 1 eindeutig
        if isinstance(result, Resolved):
            capability = result.capability
            cmdline = capability.command_key
            queue.enqueue_commands(session, [cmdline])
            return

        # 2 mehrere
        if isinstance(result, Candidates):
            await presenter.views.emit(
                "choose",
                query=query,
                candidates=[
                    {
                        "command_key": c.command_key,
                        "controller_id": c.controller_id,
                        "score": c.score,
                        "reason": c.reason,
                    }
                    for c in result.items
                ],
            )
            return

        # 3 nichts gefunden
        await presenter.views.emit("not_found", query=query)
