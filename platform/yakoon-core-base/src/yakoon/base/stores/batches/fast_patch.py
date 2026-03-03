from __future__ import annotations

from dataclasses import dataclass

from yakoon.base.ports import PatchError
from yakoon.base.stores.event.entity import JsonValue

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

    def apply(self, state: JsonValue | None, patch: JsonValue) -> JsonValue:
        self.validate(patch)

        if not isinstance(patch, dict):
            raise PatchError("FastPatch must be an object.")

        patch_dict = patch  # now narrowed to dict[str, JsonValue]

        if state is None:
            cur: dict[str, JsonValue] = {}
        else:
            if not isinstance(state, dict):
                raise PatchError("FastPatch requires object state (dict).")
            cur = dict(state)

        if "set" in patch_dict:
            s = patch_dict["set"]
            if not isinstance(s, dict):
                raise PatchError("'set' must be an object.")
            cur.update(s)

        if "unset" in patch_dict:
            u = patch_dict["unset"]
            if not isinstance(u, list):
                raise PatchError("'unset' must be a list.")
            for k in u:
                if not isinstance(k, str):
                    raise PatchError("unset entries must be strings.")
                cur.pop(k, None)

        return cur
