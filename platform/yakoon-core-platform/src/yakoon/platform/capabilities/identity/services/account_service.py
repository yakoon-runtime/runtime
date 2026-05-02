from __future__ import annotations

from yakoon.base.capabilities.identity import Account, AccountData
from yakoon.base.naming import Key, Namespace
from yakoon.base.runtime.container import Container
from yakoon.storage.eventstore.models.entity import (
    IndexKey,
    IndexSpec,
    IndexTerm,
    JsonValue,
    SnapshotHint,
    ValueType,
)


def expect_object(value: JsonValue) -> dict[str, JsonValue]:
    if not isinstance(value, dict):
        raise TypeError(f"Expected JSON object, got {type(value).__name__}")
    return value


IDX_ACCOUNT_USERNAME_KEY = IndexKey("account.username")
IDX_ACCOUNT_USERNAME_SPEC = IndexSpec(
    key=IDX_ACCOUNT_USERNAME_KEY,
    value_type=ValueType.TEXT,
    unique=True,
)


class DefaultAccountService:
    """
    Loads/saves accounts via ES-light EntityStore.
    Keeps the public API stable.
    """

    def __init__(self, container: Container) -> None:
        self.container = container
        self._store: EntityStore | None = None

    @property
    def store(self) -> EntityStore:
        if not self._store:
            self._store = self.container.get(EntityStore)
        return self._store

    async def get_by_key(self, key: Key) -> Account | None:
        row = await self.store.get_one(key=key)
        if row.data is None:
            return None

        data = AccountData.from_dict(expect_object(row.data))
        return Account(data)

    async def get_by_username(
        self, namespace: Namespace, username: str
    ) -> Account | None:

        keys, _ = await self.store.scan(
            namespace=namespace,
            index_key=IDX_ACCOUNT_USERNAME_KEY,
            value=username,
            limit=1,
            cursor=None,
        )
        if not keys:
            return None

        row = await self.store.get_one(key=keys[0])
        if row.data is None:
            return None

        data = AccountData.from_dict(expect_object(row.data))
        return Account(data)

    async def save(self, account: Account) -> None:
        key = account.data.key

        doc: JsonValue = account.data.to_dict()

        # index-on-write: username
        username = doc.get("username")
        if not isinstance(username, str):
            raise TypeError("Account.username must be a string")

        await self.store.put_doc(
            key=key,
            doc=doc,
            indexes=[IndexTerm(key=IDX_ACCOUNT_USERNAME_KEY, value=username)],
            snapshot_hint=SnapshotHint.COMMIT,
        )

    async def delete_by_key(self, key: Key) -> None:
        # ES-light delete semantics: either tombstone or hard-delete.
        # For now: write a tombstone field (recommended), or implement backend delete later.

        patch: JsonValue = [{"op": "add", "path": "/_deleted", "value": True}]

        await self.store.put(
            key=key,
            patch=patch,
            snapshot_hint=SnapshotHint.COMMIT,
        )
