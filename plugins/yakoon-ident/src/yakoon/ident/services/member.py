from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime
from typing import Protocol

from yakoon.base.naming import Key, Namespace
from yakoon.storage.eventstore.models import (
    GetResult,
    IndexKey,
    IndexTerm,
    IndexValue,
    JsonValue,
    PutResult,
    SnapshotHint,
)

from ..models import Membership

IDX_MEMBERSHIP_USER_ACCOUNT = IndexKey("membership.user_account")


class MembershipService:
    def __init__(
        self,
        on_append: OnAppend,
        on_replace: OnReplace,
        on_get_by_key: OnGetByKey,
        on_scan: OnScan,
    ):
        self.on_append = on_append
        self.on_replace = on_replace
        self.on_get_by_key = on_get_by_key
        self.on_scan = on_scan

    async def get(self, user_key: Key, account_key: Key) -> Membership | None:

        keys, _ = await self.on_scan(
            namespace=user_key.namespace,
            index_key=IDX_MEMBERSHIP_USER_ACCOUNT,
            value=f"{user_key}::{account_key}",
            limit=1,
        )
        if not keys:
            return None

        row = await self.on_get_by_key(key=keys[0])
        if not row.ok:
            return None

        return Membership.from_row(row=row)

    async def save(self, membership: Membership) -> None:
        key = membership.key
        doc = membership.data.to_dict()

        index_value = f"{membership.user_id}:{membership.account_id}"

        await self.on_replace(
            key=key,
            doc=doc,
            indexes=[
                IndexTerm(
                    key=IDX_MEMBERSHIP_USER_ACCOUNT,
                    value=index_value,
                )
            ],
            snapshot_hint=SnapshotHint.COMMIT,
        )


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


class OnGetByKey(Protocol):
    async def __call__(
        self,
        *,
        key: Key,
        at_time: datetime | None = None,
    ) -> GetResult: ...


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
