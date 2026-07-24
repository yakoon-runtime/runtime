from __future__ import annotations

from collections.abc import Callable

from yak.distribution.models import Distribution, PackName


class Resolver:
    def __init__(
        self,
        resolve_distribution: Callable[[str], Distribution | None],
    ) -> None:
        self._resolve_distribution = resolve_distribution

    def resolve(self, distribution: Distribution) -> list[PackName]:
        seen: set[PackName] = set()
        order: list[PackName] = []
        self._resolve_tree(distribution, seen, order)
        return order

    def _resolve_tree(
        self,
        dist: Distribution,
        seen: set[PackName],
        order: list[PackName],
    ) -> None:
        for sub_ref in dist.distributions:
            sub = self._resolve_distribution(sub_ref.name)
            if sub is not None:
                self._resolve_tree(sub, seen, order)

        for pack_ref in dist.packs:
            if pack_ref.name not in seen:
                seen.add(pack_ref.name)
                order.append(pack_ref.name)
