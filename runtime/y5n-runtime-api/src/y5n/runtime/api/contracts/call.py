from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class Call:
    """A protocol-level invocation request.

    Serialized as JSON by the SDK, sent through the Host
    to the Runtime for dispatch.
    """

    port: str
    method: str
    args: dict[str, Any] = field(default_factory=dict)
    caller_path: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Call:
        return cls(
            port=data.get("port", ""),
            method=data.get("method", ""),
            args=data.get("args", {}),
            caller_path=data.get("caller_path", ""),
        )

    def to_dict(self) -> dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}
