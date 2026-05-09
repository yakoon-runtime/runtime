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

from ..models import Membership, MembershipData

# ----------------------------------
# INDEX
# ----------------------------------

IDX_MEMBERSHIP_USER_KEY = IndexKey("membership.user_key")
IDX_MEMBERSHIP_USER_SPEC = IndexSpec(
    key=IDX_MEMBERSHIP_USER_KEY,
    value_type=ValueType.TEXT,
    unique=False,
)

IDX_MEMBERSHIP_GROUP_KEY = IndexKey("membership.group_key")
IDX_MEMBERSHIP_GROUP_SPEC = IndexSpec(
    key=IDX_MEMBERSHIP_GROUP_KEY,
    value_type=ValueType.TEXT,
    unique=False,
)


# ----------------------------------
# SERVICE
# ----------------------------------


class MembershipService:

    @staticmethod
    def index_specs():
        return [
            IDX_MEMBERSHIP_USER_SPEC,
            IDX_MEMBERSHIP_GROUP_SPEC,
        ]

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

    # ----------------------------------
    # API
    # ----------------------------------

    async def get_by_key(
        self,
        key: Key,
    ) -> Membership | None:

        row = await self.on_get(key=key)

        if not row.ok:
            return None

        return Membership.from_row(row=row)

    async def get_by_user_and_group(
        self,
        *,
        namespace: Namespace,
        user_key: Key,
        group_key: Key,
    ) -> Membership | None:

        key = Membership.build_key(
            namespace=namespace,
            user_key=user_key,
            group_key=group_key,
        )

        return await self.get_by_key(key)

    async def list_memberships(
        self,
        *,
        namespace: Namespace,
    ) -> list[Membership]:

        keys, _ = await self.on_scan(
            namespace=namespace,
            index_key=IDX_MEMBERSHIP_USER_KEY,
        )

        rows = await self.on_get_many(keys=keys)

        memberships = [Membership.from_row(row) for row in rows if row.ok]
        return [m for m in memberships if m.data.enabled]

    async def list_user_memberships(
        self,
        *,
        namespace: Namespace,
        user_key: Key,
    ) -> list[Membership]:

        keys, _ = await self.on_scan(
            namespace=namespace,
            index_key=IDX_MEMBERSHIP_USER_KEY,
            value=str(user_key),
        )

        rows = await self.on_get_many(keys=keys)

        memberships = [Membership.from_row(row) for row in rows if row.ok]
        return [m for m in memberships if m.data.enabled]

    async def list_group_memberships(
        self,
        *,
        namespace: Namespace,
        group_key: Key,
    ) -> list[Membership]:

        keys, _ = await self.on_scan(
            namespace=namespace,
            index_key=IDX_MEMBERSHIP_GROUP_KEY,
            value=str(group_key),
        )

        rows = await self.on_get_many(keys=keys)

        memberships = [Membership.from_row(row) for row in rows if row.ok]
        return [m for m in memberships if m.data.enabled]

    async def save(
        self,
        membership: Membership,
    ) -> None:

        doc = membership.data.to_dict()

        user_key = doc.get("user_key")
        group_key = doc.get("group_key")

        if not isinstance(user_key, str):
            raise TypeError("Membership.user_key must be a string")

        if not isinstance(group_key, str):
            raise TypeError("Membership.group_key must be a string")

        await self.on_replace(
            key=membership.key,
            doc=doc,
            indexes=[
                IndexTerm(
                    key=IDX_MEMBERSHIP_USER_KEY,
                    value=user_key,
                ),
                IndexTerm(
                    key=IDX_MEMBERSHIP_GROUP_KEY,
                    value=group_key,
                ),
            ],
            snapshot_hint=SnapshotHint.COMMIT,
        )

    # ----------------------------------
    # CONNECTION USER / GROUP
    # ----------------------------------

    async def add_membership(
        self,
        *,
        namespace: Namespace,
        user_key: Key,
        group_key: Key,
    ) -> Membership:

        key = Membership.build_key(
            namespace=namespace,
            user_key=user_key,
            group_key=group_key,
        )

        membership = Membership(
            key=key,
            data=MembershipData(
                user_key=user_key,
                group_key=group_key,
                enabled=True,
            ),
        )

        await self.save(membership)
        return membership

    async def remove_membership(
        self,
        *,
        namespace: Namespace,
        user_key: Key,
        group_key: Key,
    ) -> Membership:

        membership = await self.get_by_user_and_group(
            namespace=namespace,
            user_key=user_key,
            group_key=group_key,
        )

        if not membership:
            raise ValueError("Membership not found")

        membership.data.enabled = False

        await self.save(membership)
        return membership


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
