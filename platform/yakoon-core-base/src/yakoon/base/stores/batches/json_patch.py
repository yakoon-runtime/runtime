from __future__ import annotations

from dataclasses import dataclass

from yakoon.base.ports import PatchError
from yakoon.base.stores.event.entity import JsonValue

# ----------------------------
# Strategy 1: RFC 6902 JSON Patch
# ----------------------------


@dataclass(frozen=True, slots=True)
class JsonPatchStrategy:
    """
    RFC 6902 using the third-party 'jsonpatch' library.
    """

    # Optional: limit ops to keep CPU predictable
    max_ops: int = 50

    def validate(self, patch: JsonValue) -> None:
        # We validate shape cheaply here; jsonpatch will validate deeper on apply.
        if not isinstance(patch, list):
            raise PatchError("RFC6902 patch must be a list of operations.")
        if len(patch) > self.max_ops:
            raise PatchError(f"Patch has too many ops: {len(patch)} > {self.max_ops}.")
        for op in patch:
            if not isinstance(op, dict):
                raise PatchError("Each patch operation must be an object.")
            if "op" not in op or "path" not in op:
                raise PatchError("Each op must include 'op' and 'path'.")

    def apply(self, state: JsonValue | None, patch: JsonValue) -> JsonValue:
        self.validate(patch)

        try:
            import jsonpatch  # type: ignore
        except Exception as e:  # pragma: no cover
            raise PatchError("jsonpatch library not installed.") from e

        base = {} if state is None else state
        try:
            # in_place=False => returns a new object
            return jsonpatch.apply_patch(base, patch, in_place=False)
        except Exception as e:
            raise PatchError(f"Failed to apply RFC6902 patch: {e}") from e
