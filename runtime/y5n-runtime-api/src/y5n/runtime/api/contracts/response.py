from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class Response:
    """A protocol-level invocation result.

    Serialized as JSON by the Runtime, sent back through
    the Host to the SDK.
    """

    result: Any = None
    error: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Response:
        return cls(
            result=data.get("result"),
            error=data.get("error"),
        )

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["result"] = self.result
        return {k: v for k, v in d.items() if v is not None}
