from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from ..models import JsonValue, PatchFormat
from .errors import PatchError

# ----------------------------
# Strategy 2: FastPatch (flat-entity friendly)
# ----------------------------


@dataclass(frozen=True, slots=True)
class FastPatchStrategy:
    """
    A minimal patch format optimized for flat JSON objects.

    Patch format:
      {
        "set": {"age": 31, "segment": "A"},
        "unset": ["old_field"]
      }

    Rules:
      - state must be a JSON object (dict)
      - 'set' values must be JSON-serializable (you can relax/tighten)
      - 'unset' removes keys if present
    """

    @property
    def format(self) -> PatchFormat:
        return PatchFormat.FASTPATCH

    max_set_keys: int = 200
    max_unset_keys: int = 200

    def validate(self, patch: JsonValue) -> None:
        if not isinstance(patch, dict):
            raise PatchError("FastPatch must be an object.")
        allowed = {"set", "unset"}
        unknown = set(patch.keys()) - allowed
        if unknown:
            raise PatchError(f"FastPatch has unknown keys: {sorted(unknown)}")

        if "set" in patch:
            s = patch["set"]
            if not isinstance(s, dict):
                raise PatchError("'set' must be an object.")
            if len(s) > self.max_set_keys:
                raise PatchError(f"Too many set keys: {len(s)} > {self.max_set_keys}")

        if "unset" in patch:
            u = patch["unset"]
            if not isinstance(u, list) or any(not isinstance(x, str) for x in u):
                raise PatchError("'unset' must be a list of strings.")
            if len(u) > self.max_unset_keys:
                raise PatchError(
                    f"Too many unset keys: {len(u)} > {self.max_unset_keys}"
                )

    def apply(self, current: JsonValue | None, patch: JsonValue) -> JsonValue:
        self.validate(patch)

        if current is None or not isinstance(current, dict):
            cur: dict[str, JsonValue] = {}
        else:
            cur = dict(current)

        if not isinstance(patch, dict):
            raise TypeError("FastPatch must be an object")

        if patch.get("full") is True:
            set_doc = patch.get("set", {})
            if not isinstance(set_doc, dict):
                raise TypeError("FastPatch full requires set object")
            return dict(set_doc)

        set_fields = patch.get("set")
        if isinstance(set_fields, dict):
            for k, v in set_fields.items():
                cur[str(k)] = v

        del_fields = patch.get("del")
        if isinstance(del_fields, list):
            for k in del_fields:
                if isinstance(k, str):
                    cur.pop(k, None)

        return cur

    def create_full_replace(
        self,
        *,
        current: JsonValue | None,
        new_doc: Mapping[str, JsonValue],
    ) -> JsonValue:
        return {"full": True, "set": dict(new_doc)}

    def create_partial_update(
        self,
        *,
        current: JsonValue | None,
        fields: Mapping[str, JsonValue],
    ) -> JsonValue:
        return {"set": dict(fields)}

    def create_delete(
        self,
        *,
        current: JsonValue | None,
        fields: Sequence[str],
    ) -> JsonValue:
        return {"del": list(fields)}
