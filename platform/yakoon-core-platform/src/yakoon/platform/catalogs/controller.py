from __future__ import annotations

from collections.abc import Sequence

from yakoon.base.catalogs import (
    ControllerCatalog,
    ControllerInfo,
)


class DefaultControllerCatalogService:
    """
    Read-only snapshot about controller metadata.
    No controller instance, no directory references.
    """

    def __init__(self, catalog: ControllerCatalog):
        by_id: dict[str, ControllerInfo] = {}
        for c in catalog.all():
            if c.id in by_id:
                raise ValueError(f"Duplicate controller id in catalog: {c.id}")
            by_id[c.id] = c
        self._by_id = by_id

    def ids(self) -> Sequence[str]:
        return tuple(sorted(self._by_id.keys()))

    def all(self) -> Sequence[ControllerInfo]:
        return tuple(self._by_id[cid] for cid in self.ids())

    def get(self, controller_id: str) -> ControllerInfo | None:
        return self._by_id.get(controller_id)

    def exists(self, controller_id: str) -> bool:
        return controller_id in self._by_id

    def activatable(self) -> Sequence[ControllerInfo]:
        return tuple(c for c in self.all() if c.is_activatable)

    def listed(self) -> Sequence[ControllerInfo]:
        return tuple(c for c in self.all() if c.is_listed)

    def shell(self) -> Sequence[ControllerInfo]:
        return tuple(c for c in self.all() if c.is_shell)

    def is_shell(self, controller_id: str) -> bool:
        c = self.get(controller_id)
        return bool(c and c.is_shell)

    def is_activatable(self, controller_id: str) -> bool:
        c = self.get(controller_id)
        return bool(c and c.is_activatable)

    def is_listed(self, controller_id: str) -> bool:
        c = self.get(controller_id)
        return bool(c and c.is_listed)
