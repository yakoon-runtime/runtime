from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import Protocol

from y5n.base.naming import Key
from y5nstore.event import (
    GetResult,
    JsonValue,
    PutResult,
    SnapshotHint,
)

from .identity import SessionIdentityMap
from .session import Session, SessionData


class SessionService:
    """
    Session lifecycle service.

    Responsibilities:
    - Load / create persistent SessionState via EntityStore (ES-light).
    - Hydrate a runtime Session object from that state.
    - Guarantee process-local session identity via SessionIdentityMap.
    """

    def __init__(
        self,
        on_replace: OnReplace,
        on_get: OnGet,
        identity_map: SessionIdentityMap | None = None,
    ) -> None:
        self.on_replace = on_replace
        self.on_get = on_get
        self._map = identity_map or SessionIdentityMap()

    async def get(self, key: Key) -> Session | None:
        live = self._map.get(key)
        if live:
            return live

        row = await self.on_get(key=key)
        if not row.ok:
            return None

        session = Session.from_row(row)
        self._map.put(session)
        return session

    async def get_or_create(self, key: Key, **kwargs) -> tuple[Session, bool]:
        existing = await self.get(key)
        if existing:
            return existing, False

        # Create new state (key is required)
        data = SessionData(**kwargs)
        session = Session(key=key, data=data)

        await self.on_replace(
            key=key,
            doc=data.to_dict(),
            snapshot_hint=SnapshotHint.COMMIT,
        )

        self._map.put(session)
        return session, True

    async def save(self, session: Session) -> None:
        await self.on_replace(
            key=session.key,
            doc=session.data.to_dict(),
            snapshot_hint=SnapshotHint.COMMIT,
        )

    def release(self, key: Key) -> None:
        self._map.release(key)

    def clear(self) -> None:
        self._map.clear()


# ----------------------------------
# PORTS
# ----------------------------------


class OnReplace(Protocol):
    async def __call__(
        self,
        *,
        key: Key,
        doc: Mapping[str, JsonValue],
        snapshot_hint: SnapshotHint = SnapshotHint.AUTO,
        expected_rev: int | None = None,
    ) -> PutResult: ...


class OnGet(Protocol):
    async def __call__(
        self,
        *,
        key: Key,
        at_time: datetime | None = None,
    ) -> GetResult: ...
