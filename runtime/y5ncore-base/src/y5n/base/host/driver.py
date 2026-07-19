"""
Generic host driver — drives a command coroutine via send(None).

The command yields ``Marker`` instances (see ``protocol.py``).  The
driver dispatches each marker to a registered handler and yields
the resulting Outcomes.

Markers that modify host state (e.g. ``CWD``) are handled as
*side effects* — they are executed without yielding an Outcome.

Usage:

    from y5n.base.host.driver import drive
    from y5n.base.host.protocol import MarkerKind

    async for outcome in drive(coro, {
        MarkerKind.WRITE: lambda m, first: out(resolve(m.value), mode=...),
        MarkerKind.DELAY: lambda m, _: delay(m.value),
    }):
        yield outcome
"""

from __future__ import annotations

from collections.abc import Callable, Coroutine, Mapping
from typing import Any

from y5n.base.flow.dsl import Outcome

from .protocol import Marker, MarkerKind

# A handler receives (marker, first_output) and returns an Outcome.
_Handler = Callable[[Marker, bool], Outcome]
# A side effect receives (marker.value) and returns None.
_SideEffect = Callable[[Any], None]


__all__ = ["drive"]


async def drive(
    coro: Coroutine[Any, None, None],
    handlers: Mapping[MarkerKind, _Handler],
    side_effects: Mapping[MarkerKind, _SideEffect] | None = None,
    visual_kinds: frozenset[MarkerKind] = frozenset(
        {MarkerKind.WRITE, MarkerKind.ERROR}
    ),
):
    """Drive *coro*, yielding Outcomes from dispatched markers.

    Parameters
    ----------
    coro:
        An async function (coroutine) whose awaited capabilities
        yield ``Marker`` instances.
    handlers:
        Mapping from ``MarkerKind`` to ``handler(marker, first) -> Outcome``.
        Unhandled kinds are silently skipped (unless in *side_effects*).
    side_effects:
        Mapping from ``MarkerKind`` to ``fn(value) -> None``.
        These markers are executed without yielding an Outcome.
    visual_kinds:
        Kinds whose first occurrence switches the output mode
        from ``"replace"`` to ``"append"``.
    """
    first = True
    try:
        marker: Marker = coro.send(None)
        while True:
            if side_effects and marker.kind in side_effects:
                side_effects[marker.kind](marker.value)
            else:
                handler = handlers.get(marker.kind)
                if handler is not None:
                    yield handler(marker, first)
                    if marker.kind in visual_kinds:
                        first = False
            marker = coro.send(None)
    except StopIteration:
        pass
