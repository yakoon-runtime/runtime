from typing import Protocol

from yakoon.base.runtime.sessions import Session
from yakoon.base.values import Namespace


class NamespaceService(Protocol):
    async def from_session(
        self, session: Session, kind: str, space: str | None
    ) -> Namespace: ...


class ShardedCounterService(Protocol):
    async def next(self, prefix: str) -> str: ...
