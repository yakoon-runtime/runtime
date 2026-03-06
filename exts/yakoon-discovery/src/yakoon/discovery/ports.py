from typing import Protocol

from yakoon.base.runtime.commands import Request
from yakoon.base.runtime.sessions.session import Session
from yakoon.discovery.models.discovery import DiscoveryResult
from yakoon.discovery.models.lookup import LookupCandidatesPayload
from yakoon.discovery.models.parser import LookupIndex


class LookupParser(Protocol):

    def parse(self, text: str) -> LookupIndex: ...


class LookupCandidateStoreService:
    """
    Session-scoped short-lived store for lookup candidate lists.
    """

    def put(self, payload: LookupCandidatesPayload) -> str: ...
    def get(self, token: str) -> LookupCandidatesPayload | None: ...
    def delete(self, token: str) -> None: ...


class DiscoveryStrategy(Protocol):
    async def discover(self, session: Session, request: Request) -> DiscoveryResult: ...


class DiscoveryService:

    def register(self, priority: int, strategy: DiscoveryStrategy) -> None: ...
    async def discover(self, session: Session, request: Request) -> DiscoveryResult: ...
