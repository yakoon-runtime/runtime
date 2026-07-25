"""Provider registration — metadata only, no callables.

The ``methods`` field lists public method names as strings.
Callables stay local in the transport backend — they never
cross the JSON boundary.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class Register:
    """A provider registration request."""

    name: str
    methods: list[str] = field(default_factory=list)
    placement: str = "self"
    caller_path: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Register:
        return cls(
            name=data.get("name", ""),
            methods=data.get("methods", []),
            placement=data.get("placement", "self"),
            caller_path=data.get("caller_path", ""),
        )

    def to_dict(self) -> dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}
