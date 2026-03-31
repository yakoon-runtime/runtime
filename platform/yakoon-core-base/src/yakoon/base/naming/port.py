from typing import Protocol

from .namespace import Namespace


class Session(Protocol):
    pass


class NamespaceResolver(Protocol):
    async def from_session(
        self, session: Session, kind: str, space: str | None
    ) -> Namespace: ...


class ShardedCounterService(Protocol):
    async def next(self, prefix: str) -> str: ...
