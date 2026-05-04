from __future__ import annotations

from yakoon.base.naming import Key
from yakoon.storage.eventstore.models import (
    IndexKey,
    IndexTerm,
    SnapshotHint,
)

from ..models import Membership

IDX_MEMBERSHIP_USER_ACCOUNT = IndexKey("membership.user_account")


class MembershipService:
    def __init__(self, on_store, on_replace, on_get_by_key, on_find):
        self.on_put = on_store
        self.on_replace = on_replace
        self.on_get_by_key = on_get_by_key
        self.on_find = on_find

    async def get(self, user_key: Key, account_key: Key) -> Membership | None:

        keys, _ = await self.on_find(
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

        return Membership.from_row(row)

    async def save(self, membership: Membership) -> None:
        doc = membership.data.to_dict()

        index_value = f"{membership.user_id}:{membership.account_id}"

        await self.on_replace(
            key=membership.data.key,
            doc=doc,
            indexes=[
                IndexTerm(
                    key=IDX_MEMBERSHIP_USER_ACCOUNT,
                    value=index_value,
                )
            ],
            snapshot_hint=SnapshotHint.COMMIT,
        )
