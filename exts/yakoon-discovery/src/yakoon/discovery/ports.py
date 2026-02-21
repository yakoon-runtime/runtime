from typing import Protocol

from yakoon.base.commands.request import Request
from yakoon.base.runtime.session.session import Session
from yakoon.discovery.models.discovery import DiscoveryResult


class DiscoveryStrategy(Protocol):
    async def discover(self, session: Session, request: Request) -> DiscoveryResult: ...


class DiscoveryService:

    def register(self, priority: int, strategy: DiscoveryStrategy) -> None: ...
    async def discover(self, session: Session, request: Request) -> DiscoveryResult: ...
