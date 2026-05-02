from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import Protocol, cast

from yakoon.base.naming import Key
from yakoon.storage.eventstore import (
    GetResult,
    JsonValue,
    PutResult,
    SnapshotHint,
)

from .identity import SessionIdentityMap
from .session import Session, SessionState


class SessionManager:
    """
    Session lifecycle service.

    Responsibilities:
    - Load / create persistent SessionState via EntityStore (ES-light).
    - Hydrate a runtime Session object from that state.
    - Guarantee process-local session identity via SessionIdentityMap.
    """

    def __init__(
        self,
        on_save: OnStoreSession,
        on_load: OnLoadSession,
        identity_map: SessionIdentityMap | None = None,
    ) -> None:
        self.on_save = on_save
        self.on_load = on_load
        self._map = identity_map or SessionIdentityMap()

    async def get(self, key: Key) -> Session | None:
        live = self._map.get(key)
        if live:
            return live

        row = await self.on_load(key=key)
        if row.data is None:
            return None

        data = row.data
        if not isinstance(data, dict):
            raise TypeError(
                f"Corrupted session state: expected object, got {type(data).__name__}"
            )

        state = SessionState.from_dict(data)  # data ist JsonValue (dict)
        session = Session(state)
        self._map.put(session)
        return session

    async def get_or_create(self, key: Key, **kwargs) -> tuple[Session, bool]:
        existing = await self.get(key)
        if existing:
            return existing, False

        # Create new state (key is required)
        state = SessionState(key=key, **kwargs)
        session = Session(state)

        await self.on_save(
            key=key,
            doc=state.to_dict(),
            snapshot_hint=SnapshotHint.COMMIT,
        )

        self._map.put(session)
        return session, True

    async def save(self, session: Session) -> None:
        key = session.key
        system_session = cast(Session, session)
        await self.on_save(
            key=key,
            doc=system_session.state.to_dict(),
            snapshot_hint=SnapshotHint.COMMIT,
        )

    def release(self, key: Key) -> None:
        self._map.release(key)

    def clear(self) -> None:
        self._map.clear()


# ----------------------------------
# PORTS
# ----------------------------------


class OnStoreSession(Protocol):
    async def __call__(
        self,
        *,
        key: Key,
        doc: Mapping[str, JsonValue],
        snapshot_hint: SnapshotHint = SnapshotHint.AUTO,
        expected_rev: int | None = None,
    ) -> PutResult: ...


class OnLoadSession(Protocol):
    async def __call__(
        self,
        *,
        key: Key,
        at_time: datetime | None = None,
    ) -> GetResult: ...
