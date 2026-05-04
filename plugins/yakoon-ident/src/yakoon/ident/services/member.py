from __future__ import annotations

from yakoon.base.naming import Key
from yakoon.storage.eventstore.models import (
    IndexKey,
    IndexTerm,
    JsonValue,
    SnapshotHint,
)

from ..models import Membership, MembershipData


def expect_object(value: JsonValue) -> dict[str, JsonValue]:
    if not isinstance(value, dict):
        raise TypeError(f"Expected JSON object, got {type(value).__name__}")
    return value


IDX_MEMBERSHIP_USER_ACCOUNT = IndexKey("membership.user_account")


class MembershipService:
    def __init__(self, on_store, on_replace, on_get_by_key, on_find):
        self.on_put = on_store
        self.on_replace = on_replace
        self.on_get_by_key = on_get_by_key
        self.on_find = on_find

    async def get(self, user_id: Key, account_id: Key) -> Membership | None:
        keys, _ = await self.on_find(
            namespace=user_id.namespace,
            index_key=IDX_MEMBERSHIP_USER_ACCOUNT,
            value=f"{user_id}:{account_id}",
            limit=1,
        )
        if not keys:
            return None

        row = await self.on_get_by_key(key=keys[0])
        if row.data is None:
            return None

        return Membership(MembershipData.from_dict(expect_object(row.data)))

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
