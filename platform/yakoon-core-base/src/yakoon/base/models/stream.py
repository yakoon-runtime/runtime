from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class OutputStreaming:
    """
    Optional per-call streaming overrides.
    If a field is None, the session policy default is used.

    Commands should rarely set this. Host/session decides the default policy.
    """

    enabled: bool = True

    # stable bubble target id (optional)
    id: str | None = None

    # overrides (None => use session policy)
    interval: float | None = None
    chunk_tokens: int | None = None

    @staticmethod
    def off() -> OutputStreaming:
        return OutputStreaming(enabled=False)

    @staticmethod
    def slow(id: str | None = None) -> OutputStreaming:
        # "MUD-ish"
        return OutputStreaming(enabled=True, id=id, interval=0.12, chunk_tokens=1)


@dataclass(frozen=True, slots=True)
class OutputStreamPolicy:
    """
    Host/session-level streaming policy.
    This is the default behavior. Commands may only override via OutputStreaming.
    """

    enabled: bool = False

    # range: 0.025–0.035
    interval: float = 0.03  # ~30fps

    # range: 3–5
    chunk_tokens: int = 4  # words/whitespace chunks per tick
