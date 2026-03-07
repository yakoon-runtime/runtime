from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from yakoon.base.values import Key


class Namespace:
    """
    Represents a namespaced identifier context for addressing objects.

    Components:
    - domain: The functional domain or module (e.g., 'realm', 'minddojo')
    - kind: A specific collection or entity type (session, account, permission, invoice, npc)
    - space: Isolation boundary (tenant/workspace) — develop, acme, global

    Together, these define a unique namespace used for ID resolution, scoping, and separation.
    """

    def __init__(self, domain: str, kind: str, space: str = "global"):
        self.domain = domain
        self.kind = kind
        self.space = space

    def to_str(self) -> str:
        return f"{self.domain}/{self.kind}/{self.space}"

    def get_key(self, id: str) -> Key:
        from yakoon.base.values import Key

        return Key(self, id)

    def __eq__(self, other):
        return (
            isinstance(other, Namespace)
            and self.domain == other.domain
            and self.kind == other.kind
            and self.space == other.space
        )

    def __hash__(self):
        return hash((self.domain, self.kind, self.space))
