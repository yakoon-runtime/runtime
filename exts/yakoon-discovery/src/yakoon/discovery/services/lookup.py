import time

from yakoon.base.commands.request import Request
from yakoon.base.directories.service import ServiceDirectory
from yakoon.base.runtime.session import Session
from yakoon.discovery import ports as disc_ports
from yakoon.discovery.models.discovery import Candidates, Resolved
from yakoon.discovery.models.lookup import LookupCandidatesPayload


class LookupResolverService:

    def __init__(self, services: ServiceDirectory):
        self._services = services

    async def resolve(self, session: Session, request: Request) -> str | None:
        discovery = self._services.get(disc_ports.DiscoveryService)
        store = self._services.get(disc_ports.LookupCandidateStoreService)

        query = request.raw
        result = await discovery.discover(session, request)

        # 1 eindeutig
        if isinstance(result, Resolved):
            return result.capability.command_key

        # 2 mehrere
        if isinstance(result, Candidates):
            payload = LookupCandidatesPayload(
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
                created_at=time.time(),
            )
            token = store.put(payload)
            return f"lookup --token {token}"

        # 3 nichts
        return "lookup --token"  # oder None, je nach UX
