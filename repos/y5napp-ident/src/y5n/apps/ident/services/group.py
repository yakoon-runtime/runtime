from __future__ import annotations

from y5n.runtime.api.naming import Key, Namespace
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

from ..models import Group, GroupData

# ----------------------------------
# INDEX
# ----------------------------------

IDX_GROUP_NAME_KEY = IndexKey("group.name")
IDX_GROUP_NAME_SPEC = IndexSpec(
    key=IDX_GROUP_NAME_KEY,
    value_type=ValueType.TEXT,
    unique=True,
)

# ----------------------------------
# SERVICE
# ----------------------------------


class GroupService:

    @staticmethod
    def index_specs():
        return [IDX_GROUP_NAME_SPEC]

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

    async def get_by_key(self, key: Key) -> Group | None:
        row = await self.on_get(key=key)
        if not row.ok:
            return None

        return Group.from_row(row=row)

    async def get_by_name(self, namespace: Namespace, name: str) -> Group | None:

        keys, _ = await self.on_scan(
            namespace=namespace,
            index_key=IDX_GROUP_NAME_KEY,
            value=name,
            limit=1,
        )

        if not keys:
            return None

        row = await self.on_get(key=keys[0])
        if not row.ok:
            return None

        return Group.from_row(row=row)

    async def save(self, group: Group) -> None:
        doc = group.data.to_dict()

        name = doc.get("name")
        if not isinstance(name, str):
            raise TypeError("Group.name must be a string")

        await self.on_replace(
            key=group.key,
            doc=doc,
            indexes=[IndexTerm(key=IDX_GROUP_NAME_KEY, value=name)],
            snapshot_hint=SnapshotHint.COMMIT,
        )

    async def list_groups(self, namespace: Namespace) -> list[Group]:
        keys, _ = await self.on_scan(
            namespace=namespace,
            index_key=IDX_GROUP_NAME_KEY,
        )

        rows = await self.on_get_many(keys=keys)
        groups = [Group.from_row(row) for row in rows if row.ok]

        return [u for u in groups if u.data.enabled]

    async def add_group(
        self,
        *,
        namespace: Namespace,
        name: str,
    ) -> Group:
        key = Key(namespace=namespace, id=name)

        existing = await self.get_by_key(key)
        if existing:
            raise ValueError(f"Group already exists: {name}")

        group = Group(
            key=key,
            data=GroupData(
                name=name,
            ),
        )

        await self.save(group)
        return group

    async def edit_group(
        self,
        *,
        namespace: Namespace,
        name: str,
        changes: dict,
    ) -> Group:
        group = await self.get_by_name(namespace, name)
        if not group:
            raise ValueError(f"Group not found: {name}")

        enabled = changes.get("enabled")
        if enabled is not None:
            group.data.enabled = enabled

        await self.save(group)
        return group

    async def delete_group(
        self,
        *,
        namespace: Namespace,
        name: str,
    ) -> None:
        group = await self.get_by_name(namespace, name)
        if not group:
            raise ValueError(f"Group not found: {name}")

        group.data.enabled = False
        await self.save(group)
