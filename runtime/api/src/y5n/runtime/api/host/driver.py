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
import inspect
from collections.abc import Callable, Coroutine, Mapping
from typing import Any

from y5n.runtime.api.document import to_text
from y5n.runtime.api.flow.channel import Scope
from y5n.runtime.api.flow.dsl import Outcome
from y5n.runtime.api.flow.dsl import prompt as dsl_prompt
from y5n.runtime.api.flow.dsl import receive as dsl_receive
from y5n.runtime.api.flow.dsl import send as dsl_send
from y5n.runtime.api.flow.dsl import suspend as dsl_suspend
from y5n.runtime.api.runtime import Event as _Event

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
            # SDK port calls yield coroutines rather than awaiting
            # directly, so the executor can wrap them in Tasks.
            # This prevents Futures from third-party libraries
            # (asyncpg, httpx, …) leaking through send().
            if inspect.iscoroutine(val):
                result = await asyncio.ensure_future(val)
                val = coro.send(result)
                continue

            marker: Marker = val

            # PROMPT — show projection, wait for user input
            if marker.kind == MarkerKind.PROMPT:
                view = (
                    marker.value
                    if isinstance(marker.value, dict)
                    else to_text(marker.value)
                )
                yield dsl_prompt(view)
                event = yield dsl_receive()
                val = coro.send(event.payload if event else None)
                continue

            # RECEIVE — wait for event on a channel
            if marker.kind == MarkerKind.RECEIVE:
                params = marker.value or {}
                ch = params.get("channel")
                scope_val = params.get("scope")
                scope = Scope(scope_val) if isinstance(scope_val, str) else scope_val
                event = yield dsl_receive(ch, scope)
                val = coro.send(event)
                continue

            # SEND — emit event to a channel
            if marker.kind == MarkerKind.SEND:
                params = marker.value or {}
                ch = params.get("channel")
                payload = params.get("payload")
                scope_val = params.get("scope", "flow")
                scope = Scope(scope_val) if isinstance(scope_val, str) else scope_val
                ev = _Event(payload=payload)
                yield dsl_send(ch, ev, scope=scope)
                val = coro.send(None)
                continue

            # SUSPEND — suspend the current flow
            if marker.kind == MarkerKind.SUSPEND:
                event = yield dsl_suspend()
                val = coro.send(event)
                continue

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
