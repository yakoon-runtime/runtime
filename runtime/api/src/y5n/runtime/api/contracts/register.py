from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class Register:
    """A provider registration request.

    Serialized as JSON by the SDK, sent through the Host
    to the Runtime.

    ``placement`` is one of "self", "parent", "root".
    """

    name: str
    service: dict[str, Any] = field(default_factory=dict)
    placement: str = "self"
    caller_path: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Register:
        return cls(
            name=data.get("name", ""),
            service=data.get("service", {}),
            placement=data.get("placement", "self"),
            caller_path=data.get("caller_path", ""),
        )

    def to_dict(self) -> dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}
