from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Protocol

from .entity import JsonValue, PatchFormat


class PatchStrategy(Protocol):
    """
    Pure patch semantics.
    Store uses it for:
    - applying patches on write
    - replaying patches for historical get(at_time)
    """

    @property
    def format(self) -> PatchFormat: ...

    def apply(self, current: JsonValue | None, patch: JsonValue) -> JsonValue:
        """
        Apply 'patch' to 'state' and return NEW state.
        Must not mutate 'state' in-place.
        """
        ...

    def validate(self, patch: JsonValue) -> None:
        """
        Optional: raise PatchError for invalid patches
        (e.g. too many ops, invalid paths, wrong structure).
        """
        ...

    def create_full_replace(
        self,
        *,
        current: JsonValue | None,
        new_doc: Mapping[str, JsonValue],
    ) -> JsonValue: ...

    def create_partial_update(
        self,
        *,
        current: JsonValue | None,
        fields: Mapping[str, JsonValue],
    ) -> JsonValue: ...

    def create_delete(
        self,
        *,
        current: JsonValue | None,
        fields: Sequence[str],
    ) -> JsonValue: ...
