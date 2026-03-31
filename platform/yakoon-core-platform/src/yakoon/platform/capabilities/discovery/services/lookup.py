import time

from yakoon.base.capabilities.discovery import (
    Candidates,
    DiscoveryService,
    LookupCandidatesPayload,
    LookupCandidateStoreService,
    Resolved,
)
from yakoon.base.commands import Request
from yakoon.base.runtime import Container
from yakoon.platform.runtime.sessions import Session


class DefaultLookupResolverService:

    def __init__(self, container: Container):
        self._container = container

    async def resolve(self, session: Session, request: Request) -> str | None:
        discovery = self._container.get(DiscoveryService)
        store = self._container.get(LookupCandidateStoreService)

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
