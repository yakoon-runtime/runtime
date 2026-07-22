from __future__ import annotations

from y5n.api.naming import Key, Namespace
from y5n.runtime.store.event.models import (
    IndexKey,
    IndexSpec,
    IndexTerm,
    SnapshotHint,
    ValueType,
)
from y5n.runtime.store.event.ports import (
    OnAppend,
    OnGet,
    OnGetMany,
    OnReplace,
    OnScan,
)

from ..models import Join, JoinData

# ----------------------------------
# INDEX
# ----------------------------------

IDX_JOIN_USER_KEY = IndexKey("join.user_key")
IDX_JOIN_USER_SPEC = IndexSpec(
    key=IDX_JOIN_USER_KEY,
    value_type=ValueType.TEXT,
    unique=False,
)

IDX_JOIN_GROUP_KEY = IndexKey("join.group_key")
IDX_JOIN_GROUP_SPEC = IndexSpec(
    key=IDX_JOIN_GROUP_KEY,
    value_type=ValueType.TEXT,
    unique=False,
)


# ----------------------------------
# SERVICE
# ----------------------------------


class JoinService:

    @staticmethod
    def index_specs():
        return [
            IDX_JOIN_USER_SPEC,
            IDX_JOIN_GROUP_SPEC,
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
    ) -> Join | None:

        row = await self.on_get(key=key)

        if not row.ok:
            return None

        return Join.from_row(row=row)

    async def get_by_user_and_group(
        self,
        *,
        namespace: Namespace,
        user_key: Key,
        group_key: Key,
    ) -> Join | None:

        key = Join.build_key(
            namespace=namespace,
            user_key=user_key,
            group_key=group_key,
        )

        return await self.get_by_key(key)

    async def list_joins(
        self,
        *,
        namespace: Namespace,
    ) -> list[Join]:

        keys, _ = await self.on_scan(
            namespace=namespace,
            index_key=IDX_JOIN_USER_KEY,
        )

        rows = await self.on_get_many(keys=keys)

        joins = [Join.from_row(row) for row in rows if row.ok]
        return [m for m in joins if m.data.enabled]

    async def list_user_joins(
        self,
        *,
        namespace: Namespace,
        user_key: Key,
    ) -> list[Join]:

        keys, _ = await self.on_scan(
            namespace=namespace,
            index_key=IDX_JOIN_USER_KEY,
            value=str(user_key),
        )

        rows = await self.on_get_many(keys=keys)

        joins = [Join.from_row(row) for row in rows if row.ok]
        return [m for m in joins if m.data.enabled]

    async def list_group_joins(
        self,
        *,
        namespace: Namespace,
        group_key: Key,
    ) -> list[Join]:

        keys, _ = await self.on_scan(
            namespace=namespace,
            index_key=IDX_JOIN_GROUP_KEY,
            value=str(group_key),
        )

        rows = await self.on_get_many(keys=keys)

        joins = [Join.from_row(row) for row in rows if row.ok]
        return [m for m in joins if m.data.enabled]

    async def save(
        self,
        join_obj: Join,
    ) -> None:

        doc = join_obj.data.to_dict()

        user_key = doc.get("user_key")
        group_key = doc.get("group_key")

        if not isinstance(user_key, str):
            raise TypeError("Join.user_key must be a string")

        if not isinstance(group_key, str):
            raise TypeError("Join.group_key must be a string")

        await self.on_replace(
            key=join_obj.key,
            doc=doc,
            indexes=[
                IndexTerm(
                    key=IDX_JOIN_USER_KEY,
                    value=user_key,
                ),
                IndexTerm(
                    key=IDX_JOIN_GROUP_KEY,
                    value=group_key,
                ),
            ],
            snapshot_hint=SnapshotHint.COMMIT,
        )

    # ----------------------------------
    # CONNECTION USER / GROUP
    # ----------------------------------

    async def add_join(
        self,
        *,
        namespace: Namespace,
        user_key: Key,
        group_key: Key,
    ) -> Join:

        key = Join.build_key(
            namespace=namespace,
            user_key=user_key,
            group_key=group_key,
        )

        join_obj = Join(
            key=key,
            data=JoinData(
                user_key=user_key,
                group_key=group_key,
                enabled=True,
            ),
        )

        await self.save(join_obj)
        return join_obj

    async def remove_join(
        self,
        *,
        namespace: Namespace,
        user_key: Key,
        group_key: Key,
    ) -> Join:

        join_obj = await self.get_by_user_and_group(
            namespace=namespace,
            user_key=user_key,
            group_key=group_key,
        )

        if not join_obj:
            raise ValueError("Join not found")

        join_obj.data.enabled = False

        await self.save(join_obj)
        return join_obj


# ----------------------------------
# PORTS
# ----------------------------------
