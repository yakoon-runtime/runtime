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

    def apply(self, state: JsonValue | None, patch: JsonValue) -> JsonValue:
        last: Exception | None = None
        for s in self.strategies:
            try:
                s.validate(patch)
                return s.apply(state, patch)
            except Exception as e:
                last = e
        raise PatchError(f"No strategy could apply patch: {last}")
