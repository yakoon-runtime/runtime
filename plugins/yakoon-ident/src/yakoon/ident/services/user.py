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

from ..models import User

# ----------------------------------
# INDEX
# ----------------------------------

IDX_USER_USERNAME_KEY = IndexKey("user.username")
IDX_USER_USERNAME_SPEC = IndexSpec(
    key=IDX_USER_USERNAME_KEY,
    value_type=ValueType.TEXT,
    unique=True,
)

# ----------------------------------
# SERVICE
# ----------------------------------


class UserService:

    @staticmethod
    def index_specs():
        return [IDX_USER_USERNAME_SPEC]

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

    async def get_by_key(self, key: Key) -> User | None:
        row = await self.on_get_by_key(key=key)
        if not row.ok:
            return None

        return User.from_row(row)

    async def get_by_username(self, namespace: Namespace, username: str) -> User | None:

        keys, _ = await self.on_find(
            namespace=namespace,
            index_key=IDX_USER_USERNAME_KEY,
            value=username,
            limit=1,
        )

        if not keys:
            return None

        row = await self.on_get_by_key(key=keys[0])
        if not row.ok:
            return None

        return User.from_row(row)

    async def save(self, user: User) -> None:
        doc = user.data.to_dict()

        username = doc.get("username")
        if not isinstance(username, str):
            raise TypeError("User.username must be a string")

        await self.on_replace(
            key=user.key,
            doc=doc,
            indexes=[IndexTerm(key=IDX_USER_USERNAME_KEY, value=username)],
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
