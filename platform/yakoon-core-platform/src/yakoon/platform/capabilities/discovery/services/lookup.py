import time

from yakoon.base.capabilities.discovery.discovery import Candidates, Resolved
from yakoon.base.capabilities.discovery.lookup import LookupCandidatesPayload
from yakoon.base.capabilities.discovery.port import (
    DiscoveryService,
    LookupCandidateStoreService,
)
from yakoon.base.runtime import Request, Session
from yakoon.base.runtime.services import ServiceDirectory


class DefaultLookupResolverService:

    def __init__(self, services: ServiceDirectory):
        self._services = services

    async def resolve(self, session: Session, request: Request) -> str | None:
        discovery = self._services.get(DiscoveryService)
        store = self._services.get(LookupCandidateStoreService)

        query = request.raw
        result = await discovery.discover(session, request)

        # 1 eindeutig
        if isinstance(result, Resolved):
            return result.capability.command_key

        # 2 mehrere
        if isinstance(result, Candidates) and result.items:
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

        return None
