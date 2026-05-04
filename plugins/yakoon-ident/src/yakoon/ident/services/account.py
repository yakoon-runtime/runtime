from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime
from typing import Protocol

from yakoon.base.naming import Key, Namespace
from yakoon.storage.eventstore.models import (
    GetResult,
    IndexKey,
    IndexSpec,
    IndexTerm,
    IndexValue,
    JsonValue,
    PutResult,
    SnapshotHint,
    ValueType,
)

from ..models import Account, AccountData


def expect_object(value: JsonValue) -> dict[str, JsonValue]:
    if not isinstance(value, dict):
        raise TypeError(f"Expected JSON object, got {type(value).__name__}")
    return value


# ----------------------------------
# INDEX
# ----------------------------------

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

    def __init__(
        self,
        on_store: OnStore,
        on_replace: OnReplace,
        on_get_by_key: OnGetByKey,
        on_find: OnFind,
    ):
        self.on_put = on_store
        self.on_replace = on_replace
        self.on_get_by_key = on_get_by_key
        self.on_find = on_find

    async def get_by_key(self, key: Key) -> Account | None:
        row = await self.on_get_by_key(key=key)
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

        await self.on_replace(
            key=key,
            doc=doc,
            indexes=[IndexTerm(key=IDX_ACCOUNT_USERNAME_KEY, value=username)],
            snapshot_hint=SnapshotHint.COMMIT,
        )

    async def delete_by_key(self, key: Key) -> None:
        # ES-light delete semantics: either tombstone or hard-delete.
        # For now: write a tombstone field (recommended), or implement backend delete later.

        patch: JsonValue = {"op": "add", "path": "/_deleted", "value": True}

        await self.on_put(
            key=key,
            patch=[patch],
            snapshot_hint=SnapshotHint.COMMIT,
        )


# ----------------------------------
# PORTS
# ----------------------------------


class OnStore(Protocol):
    async def __call__(
        self,
        *,
        key: Key,
        patch: JsonValue,
        indexes: Sequence[IndexTerm] = (),
        snapshot_hint: SnapshotHint = SnapshotHint.AUTO,
        meta: Mapping[str, object] | None = None,
        expected_rev: int | None = None,
    ) -> PutResult: ...


class OnReplace(Protocol):
    async def __call__(
        self,
        *,
        key: Key,
        doc: Mapping[str, JsonValue],
        indexes: Sequence[IndexTerm] = (),
        snapshot_hint: SnapshotHint = SnapshotHint.AUTO,
        expected_rev: int | None = None,
    ) -> PutResult: ...


class OnGetByName(Protocol):
    async def __call__(
        self,
        *,
        key: Key,
        at_time: datetime | None = None,
    ) -> GetResult: ...


class OnGetByKey(Protocol):
    async def __call__(
        self,
        *,
        key: Key,
        at_time: datetime | None = None,
    ) -> GetResult: ...


class OnFind(Protocol):
    async def __call__(
        self,
        *,
        namespace: Namespace,
        index_key: IndexKey,
        value: IndexValue | None = None,
        lo: IndexValue | None = None,
        hi: IndexValue | None = None,
        limit: int = 100,
        prefix: str | None = None,
        cursor: str | None = None,
    ) -> tuple[list[Key], str | None]: ...
