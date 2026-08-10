"""Port invocation ABI — how nodes talk to each other.

This is one of the three ABIs of the Runtime API:

* ``context.py`` — the invocation ABI: which data describes the current call.
* ``invoke.py`` — the port ABI: which capability is being called.
* ``flow/`` — the flow ABI: how an execution advances (Pulse, AwaitEvent, ...).

The port ABI is the contract between two nodes: a ``Call`` names the port and
method, ``invoke()`` dispatches it through the Runtime Bus, and a ``Response``
carries the result. ``Call`` and ``Response`` are plain data carriers; the
contract itself is ``await invoke(call)``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class Call:
    """A protocol-level invocation request."""

    port: str
    method: str
    args: dict | None = None
    caller_path: str | None = None
    caller_session_key: str | None = None
    store_name: str | None = None


@dataclass
class Response:
    """A protocol-level invocation result."""

    result: Any = None
    error: str | None = None


async def invoke(call: Call) -> Response:
    """Execute a Call through the Runtime Bus.

    The bus routes to CallHandler, which resolves the provider
    and delivers the call via the executor's transport.
    """
    from y5n.runtime.api.runtime.bus import get_bus

    return await get_bus().async_dispatch(call)
