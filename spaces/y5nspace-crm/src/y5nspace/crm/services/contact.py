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

from ..models import Contact, ContactData

IDX_CONTACT_NAME_KEY = IndexKey("contact.name")
IDX_CONTACT_NAME_SPEC = IndexSpec(
    key=IDX_CONTACT_NAME_KEY,
    value_type=ValueType.TEXT,
    unique=False,
)

IDX_CONTACT_COMPANY_KEY = IndexKey("contact.company")
IDX_CONTACT_COMPANY_SPEC = IndexSpec(
    key=IDX_CONTACT_COMPANY_KEY,
    value_type=ValueType.TEXT,
    unique=False,
)


class ContactService:

    @staticmethod
    def index_specs():
        return [IDX_CONTACT_NAME_SPEC, IDX_CONTACT_COMPANY_SPEC]

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

    async def get_by_key(self, key: Key) -> Contact | None:
        row = await self.on_get(key=key)
        if not row.ok:
            return None
        return Contact.from_row(row=row)

    async def get_by_name(self, namespace: Namespace, name: str) -> Contact | None:
        keys, _ = await self.on_scan(
            namespace=namespace,
            index_key=IDX_CONTACT_NAME_KEY,
            value=name,
            limit=1,
        )
        if not keys:
            return None
        row = await self.on_get(key=keys[0])
        if not row.ok:
            return None
        return Contact.from_row(row=row)

    async def save(self, contact: Contact) -> None:
        doc = contact.data.to_dict()
        name = doc.get("name")
        if not isinstance(name, str):
            raise TypeError("Contact.name must be a string")

        company = doc.get("company", "")
        indexes = [IndexTerm(key=IDX_CONTACT_NAME_KEY, value=name)]
        if company:
            indexes.append(IndexTerm(key=IDX_CONTACT_COMPANY_KEY, value=company))

        await self.on_replace(
            key=contact.key,
            doc=doc,
            indexes=indexes,
            snapshot_hint=SnapshotHint.COMMIT,
        )

    async def list_contacts(self, namespace: Namespace) -> list[Contact]:
        keys, _ = await self.on_scan(
            namespace=namespace,
            index_key=IDX_CONTACT_NAME_KEY,
        )
        rows = await self.on_get_many(keys=keys)
        return [Contact.from_row(row) for row in rows if row.ok]

    async def add_contact(
        self,
        *,
        namespace: Namespace,
        name: str,
        company: str = "",
        email: str = "",
        phone: str = "",
        street: str = "",
        zip: str = "",
        city: str = "",
        country: str = "",
        notes: str = "",
    ) -> Contact:
        key = Key(namespace=namespace, id=name)

        existing = await self.get_by_key(key)
        if existing:
            raise ValueError(f"Contact already exists: {name}")

        now = datetime.now().isoformat()
        contact = Contact(
            key=key,
            data=ContactData(
                name=name,
                company=company,
                email=email,
                phone=phone,
                street=street,
                zip=zip,
                city=city,
                country=country,
                notes=notes,
                created_at=now,
                updated_at=now,
            ),
        )
        await self.save(contact)
        return contact

    async def edit_contact(
        self,
        *,
        namespace: Namespace,
        name: str,
        changes: dict,
    ) -> Contact:
        contact = await self.get_by_name(namespace, name)
        if not contact:
            raise ValueError(f"Contact not found: {name}")

        for field in ("company", "email", "phone", "street", "zip", "city", "country", "notes"):
            if field in changes:
                setattr(contact.data, field, changes[field])

        contact.data.updated_at = datetime.now().isoformat()
        await self.save(contact)
        return contact

    async def delete_contact(
        self,
        *,
        namespace: Namespace,
        name: str,
    ) -> None:
        contact = await self.get_by_name(namespace, name)
        if not contact:
            raise ValueError(f"Contact not found: {name}")

        # Soft-delete via store removal
        await self.on_replace(
            key=contact.key,
            doc={"name": contact.data.name, "deleted": True},
            indexes=[IndexTerm(key=IDX_CONTACT_NAME_KEY, value=contact.data.name)],
            snapshot_hint=SnapshotHint.COMMIT,
        )


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
