from __future__ import annotations

from dataclasses import dataclass

from yakoon.base.ports import PatchError, PatchStrategy
from yakoon.base.stores.event.entity import JsonValue

# ----------------------------
# Optional: Composite Strategy (for gradual migrations)
# ----------------------------


@dataclass(frozen=True, slots=True)
class CompositePatchStrategy:
    """
    Tries multiple strategies in order. Useful if you ever need to replay
    mixed patch formats without storing a format marker per revision.

    Caveat: ambiguity is possible; prefer per-store strategy or format marker.

    RFC 6902-compatible patch generator.

    Design goal: fast + correct, not minimal diffs.
    - Full replace: replace root with entire doc (1 op)
    - Partial update: add/replace each provided top-level field (N ops)
    - Delete: remove each provided top-level field (N ops)
    """

    strategies: tuple[PatchStrategy, ...]

    def validate(self, patch: JsonValue) -> None:
        last: Exception | None = None
        for s in self.strategies:
            try:
                s.validate(patch)
                return
            except Exception as e:
                last = e
        raise PatchError(f"No strategy accepted patch: {last}")

    def apply(self, current: JsonValue | None, patch: JsonValue) -> JsonValue:
        last: Exception | None = None
        for s in self.strategies:
            try:
                s.validate(patch)
                return s.apply(current, patch)
            except Exception as e:
                last = e
        raise PatchError(f"No strategy could apply patch: {last}")
