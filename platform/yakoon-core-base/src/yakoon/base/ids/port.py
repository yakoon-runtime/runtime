from typing import Protocol

from yakoon.base.runtime.sessions import CommandSession
from yakoon.base.values import Namespace


class NamespaceService(Protocol):
    async def from_session(
        self, session: CommandSession, kind: str, space: str | None
    ) -> Namespace: ...


class ShardedCounterService(Protocol):
    async def next(self, prefix: str) -> str: ...
