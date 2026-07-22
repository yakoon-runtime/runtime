"""
Generic host driver — drives a command coroutine via send(None).

The command yields ``Marker`` instances (see ``protocol.py``).  The
driver dispatches each marker according to its kind:

* **handlers** — produce a DSL ``Outcome`` (yielded to the caller).
* **side_effects** — mutate host state, no Outcome.
* **responses** — return data to the command via ``coro.send(result)``.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable, Coroutine, Mapping
from typing import Any

from y5n.runtime.api.flow.dsl import Outcome

from .protocol import Marker, MarkerKind

# handler(marker, first) → Outcome (yielded to the drive consumer)
_Handler = Callable[[Marker, bool], Outcome]
# side_effect(value) → None (mutates host state)
_SideEffect = Callable[[Any], None]
# responder(value) → Any (sent back to the coroutine)
_Responder = Callable[[Any], Any]


__all__ = ["drive"]


async def drive(
    coro: Coroutine[Any, None, None],
    handlers: Mapping[MarkerKind, _Handler],
    side_effects: Mapping[MarkerKind, _SideEffect] | None = None,
    responses: Mapping[MarkerKind, _Responder] | None = None,
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
        Yielded to the consumer of ``drive()``.
    side_effects:
        Mapping from ``MarkerKind`` to ``fn(value) -> None``.
        Executed without yielding an Outcome.
    responses:
        Mapping from ``MarkerKind`` to ``fn(value) -> Any``.
        The return value is sent back to the coroutine via
        ``coro.send(result)``, enabling request/response patterns
        like ``flows = await runtime.scheduler.flows()``.
    visual_kinds:
        Kinds whose first occurrence switches the output mode
        from ``"replace"`` to ``"append"``.
    """
    first = True
    try:
        val: Any = coro.send(None)
        while True:
            # SDK port calls yield Tasks (see _RemoteCall in ports.py)
            # rather than awaiting directly, to prevent Futures from
            # third-party libraries (asyncpg, httpx, …) leaking through
            # the send() mechanism.
            if isinstance(val, asyncio.Task):
                result = await val
                val = coro.send(result)
                continue

            marker: Marker = val
            if side_effects and marker.kind in side_effects:
                side_effects[marker.kind](marker.value)
                val = coro.send(None)
            elif responses and marker.kind in responses:
                result = responses[marker.kind](marker.value)
                val = coro.send(result)
            else:
                handler = handlers.get(marker.kind)
                if handler is not None:
                    yield handler(marker, first)
                    if marker.kind in visual_kinds:
                        first = False
                val = coro.send(None)
    except StopIteration:
        pass
