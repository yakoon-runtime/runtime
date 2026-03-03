from __future__ import annotations

from yakoon.base.models.account import Account, AccountData
from yakoon.base.models.key import Key
from yakoon.base.models.ns import Namespace
from yakoon.base.ports import IndexRegistry
from yakoon.base.stores.event.entity import (
    DomainId,
    EntityId,
    IndexKey,
    IndexSpec,
    IndexTerm,
    JsonValue,
    SnapshotHint,
    SpaceId,
    ValueType,
)
from yakoon.platform.stores.event.store import EntityStore


def expect_object(value: JsonValue) -> dict[str, JsonValue]:
    if not isinstance(value, dict):
        raise TypeError(f"Expected JSON object, got {type(value).__name__}")
    return value


def _space_id_from_namespace(ns: Namespace) -> SpaceId:
    return SpaceId(ns.space)


def _domain_from_namespace(ns: Namespace) -> DomainId:
    return DomainId(ns.domain)


def _space_id_from_key(key: Key) -> SpaceId:
    return SpaceId(key.namespace.space)


def _domain_from_key(key: Key) -> DomainId:
    return DomainId(key.namespace.domain)


def _entity_id_from_key(key: Key) -> EntityId:
    return EntityId(str(key))


IDX_ACCOUNT_USERNAME_KEY = IndexKey("account.username")
IDX_ACCOUNT_USERNAME_SPEC = IndexSpec(
    key=IDX_ACCOUNT_USERNAME_KEY,
    value_type=ValueType.TEXT,
    unique=True,
)


class AccountService:
    """
    Loads/saves accounts via ES-light EntityStore.
    Keeps the public API stable.
    """

    def __init__(self, store: EntityStore, index: IndexRegistry | None = None) -> None:
        self.store = store
        self.index = index  # optional; can be ensured at compose/plugin-load instead

    async def get_by_key(self, key: Key) -> Account | None:
        row = await self.store.get(
            domain_id=_domain_from_key(key),
            space_id=_space_id_from_key(key),
            entity_id=_entity_id_from_key(key),
        )
        if row.data is None:
            return None

        data = AccountData.from_dict(expect_object(row.data))
        return Account(data)

    async def get_by_username(
        self, namespace: Namespace, username: str
    ) -> Account | None:
        space_id = _space_id_from_namespace(namespace)
        domain_id = _domain_from_namespace(namespace)

        ids, _ = await self.store.query(
            domain_id=domain_id,
            space_id=space_id,
            index_key=IDX_ACCOUNT_USERNAME_KEY,
            value=username,
            limit=1,
            cursor=None,
        )
        if not ids:
            return None

        row = await self.store.get(
            domain_id=domain_id,
            space_id=space_id,
            entity_id=ids[0],
        )
        if row.data is None:
            return None

        data = AccountData.from_dict(expect_object(row.data))
        return Account(data)

    async def save(self, account: Account) -> None:
        key = account.data.key
        space_id = _space_id_from_key(key)
        domain_id = _domain_from_key(key)
        entity_id = _entity_id_from_key(key)

        doc: JsonValue = account.data.to_dict()

        # simplest: full replace via RFC6902 root replace
        patch: JsonValue = [{"op": "replace", "path": "", "value": doc}]

        # index-on-write: username
        username = doc.get("username")
        if not isinstance(username, str):
            raise TypeError("Account.username must be a string")

        await self.store.put(
            domain_id=domain_id,
            space_id=space_id,
            entity_id=entity_id,
            patch=patch,
            indexes=[IndexTerm(key=IDX_ACCOUNT_USERNAME_KEY, value=username)],
            snapshot_hint=SnapshotHint.COMMIT,
        )

    async def delete_by_key(self, key: Key) -> None:
        # ES-light delete semantics: either tombstone or hard-delete.
        # For now: write a tombstone field (recommended), or implement backend delete later.
        space_id = _space_id_from_key(key)
        domain_id = _domain_from_key(key)
        entity_id = _entity_id_from_key(key)

        patch: JsonValue = [{"op": "add", "path": "/_deleted", "value": True}]

        await self.store.put(
            domain_id=domain_id,
            space_id=space_id,
            entity_id=entity_id,
            patch=patch,
            snapshot_hint=SnapshotHint.COMMIT,
        )
