"""Invocation ABI — which data describes the current call.

This is one of the three ABIs of the Runtime API:

* ``context.py`` — the invocation ABI: which data describes the current call.
* ``invoke.py`` — the port ABI: which capability is being called.
* ``flow/`` — the flow ABI: how an execution advances (Pulse, AwaitEvent, ...).

The invocation ABI answers "who am I, where do I run, with which tokens?".
The engine sets it once, before the flow starts (ADR-12 Section 4). The data
is a plain dict — the runtime only transports it; the SDK models it into its
typed ``Context`` (ADR-11).
"""

from __future__ import annotations

from collections.abc import Mapping
from contextvars import ContextVar
from dataclasses import asdict, dataclass, field
from typing import Any

_context_var: ContextVar[dict[str, Any]] = ContextVar("y5n_invocation_context")


def set_context(data: dict[str, Any]) -> None:
    """Set the invocation context for the current execution (engine-side).

    Called exactly once, before the flow starts. The data is a plain dict —
    the SDK reads the same variable and models it into its typed Context.
    """
    _context_var.set(data)


def current_context() -> dict[str, Any]:
    """Return the current raw invocation context, or an empty snapshot."""
    try:
        return _context_var.get()
    except LookupError:
        return {}


@dataclass(frozen=True, slots=True)
class Actor:
    """The account behind an event: who caused it."""

    id: str | None = None
    name: str | None = None


@dataclass(frozen=True, slots=True)
class Session:
    """The session an event happened in."""

    key: str | None = None
    security_context: str | None = None


@dataclass(frozen=True, slots=True)
class Command:
    """The invocation an event belongs to."""

    path: str | None = None
    flow_id: str | None = None
    args: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class Trace:
    """Correlation across events of one action."""

    request_id: str | None = None
    origin: str | None = None
    channel: str | None = None


@dataclass(frozen=True, slots=True)
class Context:
    """The envelope every event carries (ADR-17).

    Not an audit field — a general context each event possesses. Derived
    from the invocation ABI (``derive_invocation_context``), persisted
    beside every store revision.
    """

    actor: Actor = field(default_factory=Actor)
    session: Session = field(default_factory=Session)
    command: Command = field(default_factory=Command)
    trace: Trace = field(default_factory=Trace)

    @classmethod
    def from_invocation(cls, raw: Mapping[str, Any]) -> Context:
        user = raw.get("user") or {}
        sess = raw.get("session") or {}
        node = raw.get("node") or {}
        flow = raw.get("flow") or {}

        return cls(
            actor=Actor(id=user.get("id"), name=user.get("name")),
            session=Session(
                key=sess.get("key"),
                security_context=sess.get("security_context"),
            ),
            command=Command(
                path=node.get("path"),
                flow_id=flow.get("id"),
                args=tuple(raw.get("args") or []),
            ),
            trace=Trace(
                request_id=raw.get("trace_id"),
                origin=raw.get("origin"),
                channel=raw.get("channel"),
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        def clean(value: Any) -> Any:
            if isinstance(value, tuple):
                return [clean(v) for v in value]
            if isinstance(value, dict):
                return {k: clean(v) for k, v in value.items() if v is not None}
            return value

        return clean(asdict(self))


__all__ = [
    "Actor",
    "Command",
    "Context",
    "Session",
    "Trace",
    "current_context",
    "set_context",
]
