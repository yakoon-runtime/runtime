from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime
from typing import Protocol

from y5n.api.naming import Key, Namespace
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

from ..models import (
    PermissionGrant,
    PermissionGrantData,
)

# ----------------------------------
# INDEX
# ----------------------------------

IDX_PERMISSION_SUBJECT_KEY = IndexKey("permission.subject_key")

IDX_PERMISSION_SUBJECT_SPEC = IndexSpec(
    key=IDX_PERMISSION_SUBJECT_KEY,
    value_type=ValueType.TEXT,
    unique=False,
)

IDX_PERMISSION_KEY = IndexKey("permission.permission_key")

IDX_PERMISSION_SPEC = IndexSpec(
    key=IDX_PERMISSION_KEY,
    value_type=ValueType.TEXT,
    unique=False,
)

# ----------------------------------
# SERVICE
# ----------------------------------


class PermissionGrantService:

    @staticmethod
    def index_specs():
        return [
            IDX_PERMISSION_SUBJECT_SPEC,
            IDX_PERMISSION_SPEC,
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
    ) -> PermissionGrant | None:

        row = await self.on_get(key=key)

        if not row.ok:
            return None

        return PermissionGrant.from_row(row=row)

    async def get_by_subject_and_permission(
        self,
        *,
        namespace: Namespace,
        subject_key: Key,
        permission_key: str,
    ) -> PermissionGrant | None:

        key = PermissionGrant.build_key(
            namespace=namespace,
            subject_key=subject_key,
            permission_key=permission_key,
        )

        return await self.get_by_key(key)

    async def list_grants(
        self,
        *,
        namespace: Namespace,
    ) -> list[PermissionGrant]:

        keys, _ = await self.on_scan(
            namespace=namespace,
            index_key=IDX_PERMISSION_SUBJECT_KEY,
        )

        rows = await self.on_get_many(keys=keys)

        grants = [PermissionGrant.from_row(row) for row in rows if row.ok]

        return [g for g in grants if g.data.enabled]

    async def list_subject_grants(
        self,
        *,
        namespace: Namespace,
        subject_key: Key,
    ) -> list[PermissionGrant]:

        keys, _ = await self.on_scan(
            namespace=namespace,
            index_key=IDX_PERMISSION_SUBJECT_KEY,
            value=str(subject_key),
        )

        rows = await self.on_get_many(keys=keys)

        grants = [PermissionGrant.from_row(row) for row in rows if row.ok]

        return [g for g in grants if g.data.enabled]

    async def list_permission_grants(
        self,
        *,
        namespace: Namespace,
        permission_key: str,
    ) -> list[PermissionGrant]:

        keys, _ = await self.on_scan(
            namespace=namespace,
            index_key=IDX_PERMISSION_KEY,
            value=permission_key,
        )

        rows = await self.on_get_many(keys=keys)

        grants = [PermissionGrant.from_row(row) for row in rows if row.ok]

        return [g for g in grants if g.data.enabled]

    # ----------------------------------
    # STORAGE
    # ----------------------------------

    async def save(
        self,
        grant: PermissionGrant,
    ) -> None:

        doc = grant.data.to_dict()

        subject_key = doc.get("subject_key")
        permission_key = doc.get("permission_key")

        if not isinstance(subject_key, str):
            raise TypeError("PermissionGrant.subject_key " "must be a string")

        if not isinstance(permission_key, str):
            raise TypeError("PermissionGrant.permission_key " "must be a string")

        await self.on_replace(
            key=grant.key,
            doc=doc,
            indexes=[
                IndexTerm(
                    key=IDX_PERMISSION_SUBJECT_KEY,
                    value=subject_key,
                ),
                IndexTerm(
                    key=IDX_PERMISSION_KEY,
                    value=permission_key,
                ),
            ],
            snapshot_hint=SnapshotHint.COMMIT,
        )

    # ----------------------------------
    # COMMANDS
    # ----------------------------------

    async def add_grant(
        self,
        *,
        namespace: Namespace,
        subject_key: Key,
        permission_key: str,
        bits: str = "x",
        deny: bool = False,
    ) -> PermissionGrant:

        key = PermissionGrant.build_key(
            namespace=namespace,
            subject_key=subject_key,
            permission_key=permission_key,
        )

        grant = PermissionGrant(
            key=key,
            data=PermissionGrantData(
                subject_key=subject_key,
                permission_key=permission_key,
                bits=bits,
                deny=deny,
                enabled=True,
            ),
        )

        await self.save(grant)

        return grant

    async def remove_grant(
        self,
        *,
        namespace: Namespace,
        subject_key: Key,
        permission_key: str,
    ) -> PermissionGrant:

        grant = await self.get_by_subject_and_permission(
            namespace=namespace,
            subject_key=subject_key,
            permission_key=permission_key,
        )

        if not grant:
            raise ValueError("Permission grant not found")

        grant.data.enabled = False

        await self.save(grant)

        return grant


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
