from __future__ import annotations

from yak.distribution.models import PackName
from yak.repository.interface import Repository


class Resolver:
    def __init__(self, repository: Repository) -> None:
        self._repository = repository

    def resolve(self, distribution_name: str) -> list[PackName]:
        seen: set[PackName] = set()
        order: list[PackName] = []
        self._resolve_tree(distribution_name, seen, order)
        return order

    def _resolve_tree(
        self,
        name: str,
        seen: set[PackName],
        order: list[PackName],
    ) -> None:
        dist = self._repository.resolve_distribution(name)
        if dist is None:
            return

        for sub_ref in dist.distributions:
            self._resolve_tree(sub_ref.name, seen, order)

        for pack_ref in dist.packs:
            if pack_ref.name not in seen:
                seen.add(pack_ref.name)
                order.append(pack_ref.name)
