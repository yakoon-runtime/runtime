from __future__ import annotations

from datetime import datetime

from y5n.apps.crm.models import Contact, ContactData
from y5n.runtime.api.naming import Key, Namespace
from y5n.runtime.store.event.models import (
    IndexKey,
    IndexQueryTerm,
    IndexSpec,
    IndexTerm,
    SnapshotHint,
    ValueType,
)
from y5n.runtime.store.event.ports import (
    OnDelete,
    OnGet,
    OnGetMany,
    OnQueryIndex,
    OnReplace,
    OnScan,
)
from y5n.runtime.store.sequence import OnNextId

IDX_CONTACT_NAME_KEY = IndexKey("contact.name")
IDX_CONTACT_NAME_SPEC = IndexSpec(
    key=IDX_CONTACT_NAME_KEY, value_type=ValueType.TEXT, unique=False
)
IDX_CONTACT_COMPANY_KEY = IndexKey("contact.company")
IDX_CONTACT_COMPANY_SPEC = IndexSpec(
    key=IDX_CONTACT_COMPANY_KEY, value_type=ValueType.TEXT, unique=False
)
IDX_CONTACT_EMAIL_KEY = IndexKey("contact.email")
IDX_CONTACT_EMAIL_SPEC = IndexSpec(
    key=IDX_CONTACT_EMAIL_KEY, value_type=ValueType.TEXT, unique=False
)
IDX_CONTACT_PHONE_KEY = IndexKey("contact.phone")
IDX_CONTACT_PHONE_SPEC = IndexSpec(
    key=IDX_CONTACT_PHONE_KEY, value_type=ValueType.TEXT, unique=False
)
IDX_CONTACT_CITY_KEY = IndexKey("contact.city")
IDX_CONTACT_CITY_SPEC = IndexSpec(
    key=IDX_CONTACT_CITY_KEY, value_type=ValueType.TEXT, unique=False
)
IDX_CONTACT_COUNTRY_KEY = IndexKey("contact.country")
IDX_CONTACT_COUNTRY_SPEC = IndexSpec(
    key=IDX_CONTACT_COUNTRY_KEY, value_type=ValueType.TEXT, unique=False
)
IDX_CONTACT_STREET_KEY = IndexKey("contact.street")
IDX_CONTACT_STREET_SPEC = IndexSpec(
    key=IDX_CONTACT_STREET_KEY, value_type=ValueType.TEXT, unique=False
)
IDX_CONTACT_ZIP_KEY = IndexKey("contact.zip")
IDX_CONTACT_ZIP_SPEC = IndexSpec(
    key=IDX_CONTACT_ZIP_KEY, value_type=ValueType.TEXT, unique=False
)
IDX_CONTACT_NOTES_KEY = IndexKey("contact.notes")
IDX_CONTACT_NOTES_SPEC = IndexSpec(
    key=IDX_CONTACT_NOTES_KEY, value_type=ValueType.TEXT, unique=False
)


class ContactService:

    _FIELD_TO_INDEX_KEY: dict[str, IndexKey] = {
        "name": IDX_CONTACT_NAME_KEY,
        "company": IDX_CONTACT_COMPANY_KEY,
        "email": IDX_CONTACT_EMAIL_KEY,
        "phone": IDX_CONTACT_PHONE_KEY,
        "city": IDX_CONTACT_CITY_KEY,
        "country": IDX_CONTACT_COUNTRY_KEY,
        "street": IDX_CONTACT_STREET_KEY,
        "zip": IDX_CONTACT_ZIP_KEY,
        "notes": IDX_CONTACT_NOTES_KEY,
    }

    _INDEX_SPECS = [
        IDX_CONTACT_NAME_SPEC,
        IDX_CONTACT_COMPANY_SPEC,
        IDX_CONTACT_EMAIL_SPEC,
        IDX_CONTACT_PHONE_SPEC,
        IDX_CONTACT_CITY_SPEC,
        IDX_CONTACT_COUNTRY_SPEC,
        IDX_CONTACT_STREET_SPEC,
        IDX_CONTACT_ZIP_SPEC,
        IDX_CONTACT_NOTES_SPEC,
    ]

    def __init__(
        self,
        on_get: OnGet,
        on_replace: OnReplace,
        on_get_many: OnGetMany,
        on_scan: OnScan,
        on_delete: OnDelete,
        on_query_index: OnQueryIndex,
        on_next_id: OnNextId,
    ):
        self.on_get = on_get
        self.on_replace = on_replace
        self.on_get_many = on_get_many
        self.on_scan = on_scan
        self.on_delete = on_delete
        self.on_query_index = on_query_index
        self.on_next_id = on_next_id

    @staticmethod
    def index_specs():
        return list(ContactService._INDEX_SPECS)

    async def get_by_name(self, namespace: Namespace, name: str) -> Contact | None:
        keys, _ = await self.on_scan(
            namespace=namespace, index_key=IDX_CONTACT_NAME_KEY, value=name, limit=1
        )
        if not keys:
            return None
        row = await self.on_get(key=keys[0])
        if not row.ok:
            return None
        return Contact.from_row(row=row)

    async def list_contacts(self, namespace: Namespace) -> list[Contact]:
        keys, _ = await self.on_scan(
            namespace=namespace, index_key=IDX_CONTACT_NAME_KEY
        )
        rows = await self.on_get_many(keys=keys)
        return [Contact.from_row(row) for row in rows if row.ok]

    async def find_contacts(
        self, namespace: Namespace, **filters: str
    ) -> list[Contact]:
        terms: list[IndexQueryTerm] = []
        for field, value in filters.items():
            index_key = self._FIELD_TO_INDEX_KEY.get(field)
            if not index_key:
                raise ValueError(f"Unknown contact filter: {field}")
            if value:
                terms.append(
                    IndexQueryTerm(index_key=index_key, op="contains", value=value)
                )
        if not terms:
            return await self.list_contacts(namespace)
        keys, _ = await self.on_query_index(
            namespace=namespace, terms=terms, mode="and", limit=100
        )
        if not keys:
            return []
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
        contact_id = await self.on_next_id(prefix="contact")
        key = Key(namespace=namespace, id=contact_id)
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
        await self._save(contact)
        return contact

    async def edit_contact(
        self, *, namespace: Namespace, name: str, changes: dict
    ) -> Contact:
        contact = await self.get_by_name(namespace, name)
        if not contact:
            raise ValueError(f"Contact not found: {name}")
        for field in (
            "company",
            "email",
            "phone",
            "street",
            "zip",
            "city",
            "country",
            "notes",
        ):
            if field in changes:
                setattr(contact.data, field, changes[field])
        contact.data.updated_at = datetime.now().isoformat()
        await self._save(contact)
        return contact

    async def delete_contact(self, *, namespace: Namespace, name: str) -> None:
        contact = await self.get_by_name(namespace, name)
        if not contact:
            raise ValueError(f"Contact not found: {name}")
        await self.on_delete(key=contact.key)

    async def _save(self, contact: Contact) -> None:
        doc = contact.data.to_dict()
        indexes: list[IndexTerm] = []
        for field, idx_key in self._FIELD_TO_INDEX_KEY.items():
            val = doc.get(field, "")
            if isinstance(val, str) and val:
                indexes.append(IndexTerm(key=idx_key, value=val))
        await self.on_replace(
            key=contact.key, doc=doc, indexes=indexes, snapshot_hint=SnapshotHint.COMMIT
        )
