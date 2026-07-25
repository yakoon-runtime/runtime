from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class Context:
    """Language-neutral execution context.

    Serialized as JSON by the Runtime and passed to the Host.
    The Host forwards it to the SDK, which wraps it into
    language-native objects.

    Fields are plain data only — no handles, no services,
    no runtime references. This is a snapshot of the call's
    starting conditions.
    """

    node: dict[str, Any] = field(default_factory=dict)

    cwd: str = ""
    workspace: str = ""

    user: dict[str, Any] = field(default_factory=dict)
    session: dict[str, Any] = field(default_factory=dict)

    tokens: list[str] = field(default_factory=list)

    trace_id: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Context:
        return cls(
            node=data.get("node", {}),
            cwd=data.get("cwd", ""),
            workspace=data.get("workspace", ""),
            user=data.get("user", {}),
            session=data.get("session", {}),
            tokens=data.get("tokens", []),
            trace_id=data.get("trace_id"),
        )

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        return {k: v for k, v in d.items() if v is not None}
