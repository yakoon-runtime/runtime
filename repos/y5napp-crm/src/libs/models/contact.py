from __future__ import annotations

from dataclasses import dataclass, field

from y5n.api.naming import Key
from y5nstore.event import GetResult


@dataclass
class ContactData:
    CURRENT_VERSION = 1
    name: str
    company: str = ""
    email: str = ""
    phone: str = ""
    street: str = ""
    zip: str = ""
    city: str = ""
    country: str = ""
    notes: str = ""
    created_at: str = ""
    updated_at: str = ""
    _v: int = field(default=CURRENT_VERSION)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "company": self.company,
            "email": self.email,
            "phone": self.phone,
            "street": self.street,
            "zip": self.zip,
            "city": self.city,
            "country": self.country,
            "notes": self.notes,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "_v": self._v,
        }

    @classmethod
    def from_dict(cls, d: dict) -> ContactData:
        d = dict(d or {})
        return cls(
            name=d["name"],
            company=d.get("company", ""),
            email=d.get("email", ""),
            phone=d.get("phone", ""),
            street=d.get("street", ""),
            zip=d.get("zip", ""),
            city=d.get("city", ""),
            country=d.get("country", ""),
            notes=d.get("notes", ""),
            created_at=d.get("created_at", ""),
            updated_at=d.get("updated_at", ""),
            _v=d.get("_v", 0),
        )


class Contact:
    def __init__(self, key: Key, data: ContactData):
        self.key = key
        self.data = data

    @property
    def name(self) -> str:
        return self.data.name

    @classmethod
    def from_row(cls, row: GetResult) -> Contact:
        data = row.require_object()
        return cls(key=row.key, data=ContactData.from_dict(data))
