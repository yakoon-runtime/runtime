from y5n.base.capabilities.discovery import (
    DiscoveryResult,
    DiscoveryStrategy,
    NoMatch,
)
from y5n.base.commands import Request
from y5n.runtime.runtime.sessions import Session


class DefaultDiscoveryService:

    def __init__(self) -> None:
        self._strategies: list[tuple[int, DiscoveryStrategy]] = []

    def register(self, priority: int, strategy: DiscoveryStrategy) -> None:
        self._strategies.append((priority, strategy))
        self._strategies.sort(key=lambda x: x[0])

    async def discover(self, session: Session, request: Request) -> DiscoveryResult:
        for _, strategy in self._strategies:
            result = await strategy.discover(session, request)
            if not isinstance(result, NoMatch):
                return result
        return NoMatch()
