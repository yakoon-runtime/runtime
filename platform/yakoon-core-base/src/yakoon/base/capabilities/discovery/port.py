from __future__ import annotations

from typing import Protocol

from yakoon.base.commands import Request
from yakoon.base.runtime.sessions import Session

from .discovery import DiscoveryResult
from .lookup import LookupCandidatesPayload
from .parser import LookupIndex


class LookupResolver(Protocol):
    async def resolve(self, session: Session, request: Request) -> str | None: ...


class DiscoveryService:

    def register(self, priority: int, strategy: DiscoveryStrategy) -> None: ...
    async def discover(self, session: Session, request: Request) -> DiscoveryResult: ...


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
