from __future__ import annotations

from typing import cast

from yakoon.base.stores.event.entity import (
    SnapshotHint,
)
from yakoon.base.values import Key
from yakoon.platform.stores.event.store import EntityStore

from .identity import SessionIdentityMap
from .session import Session, SessionState


class DefaultSessionService:
    """
    Session lifecycle service.

    Responsibilities:
    - Load / create persistent SessionState via EntityStore (ES-light).
    - Hydrate a runtime Session object from that state.
    - Guarantee process-local session identity via SessionIdentityMap.
    """

    def __init__(
        self, store: EntityStore, identity_map: SessionIdentityMap | None = None
    ) -> None:
        self.store = store
        self._map = identity_map or SessionIdentityMap()

    async def get(self, key: Key) -> Session | None:
        live = self._map.get(key)
        if live:
            return live

        row = await self.store.get_one(key=key)
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

        await self.store.put_doc(
            key=key,
            doc=state.to_dict(),
            snapshot_hint=SnapshotHint.COMMIT,
        )

        self._map.put(session)
        return session, True

    async def save(self, session: Session) -> None:
        key = session.key
        system_session = cast(Session, session)
        await self.store.put_doc(
            key=key,
            doc=system_session.state.to_dict(),
            snapshot_hint=SnapshotHint.COMMIT,
        )

    def release(self, key: Key) -> None:
        self._map.release(key)

    def clear(self) -> None:
        self._map.clear()
