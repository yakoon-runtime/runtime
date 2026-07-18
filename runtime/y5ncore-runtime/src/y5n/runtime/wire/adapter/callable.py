"""Adapter: generic callable port for the Runtime Bus.

Wraps a plain callable (like tree.validate or ds.read) as a Bus adapter
so commands using the SDK can invoke it via ``ports.get(name)()``.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from y5n.base.runtime.context import Call


class CallableAdapter:
    """Wraps any callable fn so it can be registered as a Bus adapter.

    The SDK sends ``Call(port=..., method="__call__")``; the transport
    calls ``adapter.__call__(call, **args)`` which delegates to *fn*.
    """

    def __init__(self, fn: Callable[..., Any]) -> None:
        self._fn = fn

    def __call__(self, call: Call, **kwargs: Any) -> Any:
        return self._fn(**kwargs)
