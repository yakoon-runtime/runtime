from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime
from typing import Protocol

from y5n.base.naming import Key, Namespace
from y5nstore.event.models import (
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

from ..models import User, UserData

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
        on_get: OnGet,
        on_append: OnAppend,
        on_replace: OnReplace,
        on_get_many: OnGetMany,
        on_scan: OnScan,
    ):
        self.on_get = on_get
        self.on_append = on_append
        self.on_replace = on_replace
        self.on_get_many = on_get_many
        self.on_scan = on_scan

    async def get_by_key(self, key: Key) -> User | None:
        row = await self.on_get(key=key)
        if not row.ok:
            return None

        return User.from_row(row=row)

    async def get_by_username(self, namespace: Namespace, username: str) -> User | None:

        keys, _ = await self.on_scan(
            namespace=namespace,
            index_key=IDX_USER_USERNAME_KEY,
            value=username,
            limit=1,
        )

        if not keys:
            return None

        row = await self.on_get(key=keys[0])
        if not row.ok:
            return None

        return User.from_row(row=row)

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

    async def list_users(self, namespace: Namespace) -> list[User]:
        keys, _ = await self.on_scan(
            namespace=namespace,
            index_key=IDX_USER_USERNAME_KEY,
        )

        rows = await self.on_get_many(keys=keys)
        users = [User.from_row(row) for row in rows if row.ok]

        return [u for u in users if u.data.enabled]

    async def add_user(
        self,
        *,
        namespace: Namespace,
        username: str,
        password: str | None = None,
    ) -> User:
        key = Key(namespace=namespace, id=username)

        existing = await self.get_by_key(key)
        if existing:
            raise ValueError(f"User already exists: {username}")

        user = User(
            key=key,
            data=UserData(
                username=username,
                password_hash=password,
            ),
        )

        await self.save(user)
        return user

    async def edit_user(
        self,
        *,
        namespace: Namespace,
        username: str,
        changes: dict,
    ) -> User:
        user = await self.get_by_username(namespace, username)
        if not user:
            raise ValueError(f"User not found: {username}")

        password = changes.get("password")
        if password is not None:
            user.data.password_hash = password

        enabled = changes.get("enabled")
        if enabled is not None:
            user.data.enabled = enabled

        await self.save(user)
        return user

    async def delete_user(
        self,
        *,
        namespace: Namespace,
        username: str,
    ) -> None:
        user = await self.get_by_username(namespace, username)
        if not user:
            raise ValueError(f"User not found: {username}")

        user.data.enabled = False
        await self.save(user)


# ----------------------------------
# PORTS
# ----------------------------------


class OnAppend(Protocol):
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


class OnGet(Protocol):
    async def __call__(
        self,
        *,
        key: Key,
        at_time: datetime | None = None,
    ) -> GetResult: ...


class OnGetMany(Protocol):
    async def __call__(
        self,
        *,
        keys: Sequence[Key],
    ) -> list[GetResult]: ...


class OnScan(Protocol):
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
