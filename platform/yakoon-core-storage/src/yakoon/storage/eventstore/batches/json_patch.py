from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import cast

from ..models import JsonValue, PatchFormat
from .errors import PatchError

# ----------------------------
# Strategy 1: RFC 6902 JSON Patch
# ----------------------------


@dataclass(frozen=True, slots=True)
class JsonPatchStrategy:
    """
    RFC 6902 using the third-party 'jsonpatch' library.
    """

    @property
    def format(self) -> PatchFormat:
        return PatchFormat.JSONPATCH

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

    def apply(self, current: JsonValue | None, patch: JsonValue) -> JsonValue:
        self.validate(patch)

        try:
            import jsonpatch  # type: ignore
        except Exception as e:  # pragma: no cover
            raise PatchError("jsonpatch library not installed.") from e

        base: JsonValue = {} if current is None else current

        try:
            result = jsonpatch.apply_patch(base, patch, in_place=False)
        except Exception as e:
            raise PatchError(f"Failed to apply RFC6902 patch: {e}") from e

        # Boundary: externes System → wir übernehmen Kontrolle
        if not _is_json_value(result):
            raise PatchError("jsonpatch returned invalid JSON structure.")

        return cast(JsonValue, result)

    def create_full_replace(
        self,
        *,
        current: JsonValue | None,
        new_doc: Mapping[str, JsonValue],
    ) -> JsonValue:
        # Root replace (single op). Many JSON Patch libs accept "" as root.
        # If your patch applier expects "/", adjust here.
        return [{"op": "replace", "path": "", "value": dict(new_doc)}]

    def create_partial_update(
        self,
        *,
        current: JsonValue | None,
        fields: Mapping[str, JsonValue],
    ) -> JsonValue:
        ops: list[dict[str, JsonValue]] = []
        for k, v in fields.items():
            ops.append(
                {
                    "op": "add",
                    "path": f"/{_escape_json_pointer(k)}",
                    "value": v,
                }
            )
        return cast(JsonValue, ops)

    def create_delete(
        self,
        *,
        current: JsonValue | None,
        fields: Sequence[str],
    ) -> JsonValue:
        ops: list[dict[str, JsonValue]] = []
        for k in fields:
            ops.append(
                {
                    "op": "remove",
                    "path": f"/{_escape_json_pointer(k)}",
                }
            )
        return cast(JsonValue, ops)


def _escape_json_pointer(token: str) -> str:
    # RFC 6901 escaping
    return token.replace("~", "~0").replace("/", "~1")


def _is_json_value(value: object) -> bool:
    if value is None:
        return True
    if isinstance(value, (str, int, float, bool)):
        return True
    if isinstance(value, list):
        return all(_is_json_value(v) for v in value)
    if isinstance(value, dict):
        return all(isinstance(k, str) and _is_json_value(v) for k, v in value.items())
    return False
