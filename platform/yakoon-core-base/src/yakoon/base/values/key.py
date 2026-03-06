from __future__ import annotations

from yakoon.base.values.namespace import Namespace


class Key:

    def __init__(self, namespace: Namespace, id: str):
        self.namespace = namespace
        self.id = id

    @classmethod
    def from_str(cls, raw: str) -> Key:
        try:
            ns_part, id = raw.rsplit("#", 1)
            domain, bucket, scope = ns_part.split("/")
        except ValueError as exc:
            raise ValueError(f"Invalid key format: {raw}") from exc
        return Key(Namespace(domain, bucket, scope), id)

    @classmethod
    def from_parts(cls, domain: str, kind: str, space: str, id: str) -> Key:
        return cls(namespace=Namespace(domain, kind, space), id=id)

    @staticmethod
    def is_key(s: str) -> bool:
        try:
            Key.from_str(s)
            return True
        except ValueError:
            return False

    def is_valid(self) -> bool:
        ns = self.namespace
        return all([ns.domain, ns.kind, ns.space, self.id])

    def with_id(self, new_id: str) -> Key:
        return Key(namespace=self.namespace, id=new_id)

    def to_prefix(self) -> str:
        return self.namespace.to_str()

    def to_str(self):
        return str(self)

    def __str__(self):
        return f"{self.namespace.to_str()}#{self.id}"

    def __repr__(self):
        return f"<Key {self}>"

    def __eq__(self, other):
        return (
            isinstance(other, Key)
            and self.namespace == other.namespace
            and self.id == other.id
        )

    def __hash__(self):
        return hash((self.namespace.to_str(), self.id))
