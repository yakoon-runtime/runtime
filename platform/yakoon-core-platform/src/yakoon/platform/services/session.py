from __future__ import annotations

from yakoon.base.models.key import Key
from yakoon.base.runtime.session import Session, SessionState
from yakoon.base.stores.event.entity import (
    DomainId,
    EntityId,
    JsonValue,
    SnapshotHint,
    SpaceId,
)
from yakoon.platform.stores.event.store import EntityStore


class SessionIdentityMap:

    def __init__(self) -> None:
        self._live: dict[str, Session] = {}

    def get(self, key: Key) -> Session | None:
        return self._live.get(str(key))

    def put(self, session: Session) -> None:
        self._live[str(session.key)] = session

    def release(self, key: Key) -> None:
        self._live.pop(str(key), None)

    def clear(self) -> None:
        self._live.clear()


def _space_id_from_key(key: Key) -> SpaceId:
    return SpaceId(key.namespace.space)


def _domain_id_from_key(key: Key) -> DomainId:
    return DomainId(key.namespace.domain)


def _entity_id_from_key(key: Key) -> EntityId:
    return EntityId(str(key))


class SessionService:
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

        space_id = _space_id_from_key(key)
        domain_id = _domain_id_from_key(key)
        entity_id = _entity_id_from_key(key)

        row = await self.store.get(
            domain_id=domain_id,
            space_id=space_id,
            entity_id=entity_id,
        )
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

        space_id = _space_id_from_key(key)
        domain_id = _domain_id_from_key(key)
        entity_id = _entity_id_from_key(key)

        # Persist full state as a patch:
        # We keep it simple: replace each top-level field via RFC6902 ops.
        doc = state.to_dict()
        patch: JsonValue = [
            {"op": "add", "path": f"/{k}", "value": v} for k, v in doc.items()
        ]

        await self.store.put(
            domain_id=domain_id,
            space_id=space_id,
            entity_id=entity_id,
            patch=patch,
            snapshot_hint=SnapshotHint.COMMIT,
        )

        self._map.put(session)
        return session, True

    async def save(self, session: Session) -> None:
        key = session.key

        space_id = _space_id_from_key(key)
        domain_id = _domain_id_from_key(key)
        entity_id = _entity_id_from_key(key)

        doc = session.state.to_dict()
        patch: JsonValue = [
            {"op": "add", "path": f"/{k}", "value": v} for k, v in doc.items()
        ]

        await self.store.put(
            domain_id=domain_id,
            space_id=space_id,
            entity_id=entity_id,
            patch=patch,
            snapshot_hint=SnapshotHint.COMMIT,
        )

    def release(self, key: Key) -> None:
        self._map.release(key)

    def clear(self) -> None:
        self._map.clear()
