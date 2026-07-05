from __future__ import annotations

from datetime import datetime
from typing import Protocol

from y5n.api.naming import Key
from y5nstore.event.models import (
    GetResult,
    IndexKey,
    IndexSpec,
    IndexTerm,
    JsonValue,
    SnapshotHint,
    ValueType,
)
from y5nstore.event.ports import (
    OnAppend,
    OnReplace,
    OnScan,
)

from ..models import Account

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
        on_append: OnAppend,
        on_replace: OnReplace,
        on_get_by_key: OnGetByKey,
        on_scan: OnScan,
    ):
        self.on_append = on_append
        self.on_replace = on_replace
        self.on_get_by_key = on_get_by_key
        self.on_scan = on_scan

    async def get_by_key(self, key: Key) -> Account | None:
        row = await self.on_get_by_key(key=key)
        if not row.ok:
            return None

        return Account.from_row(row=row)

    async def save(self, account: Account) -> None:
        key = account.key
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

        await self.on_append(
            key=key,
            patch=[patch],
            snapshot_hint=SnapshotHint.COMMIT,
        )


# ----------------------------------
# PORTS
# ----------------------------------


class OnGetByKey(Protocol):
    async def __call__(
        self,
        *,
        key: Key,
        at_time: datetime | None = None,
    ) -> GetResult: ...
