from __future__ import annotations

from collections.abc import Callable
from typing import Any

from .context import Call
from .messages import RegisterProvider, UnregisterProvider
from .resolver import Resolver
from .transport import DirectTransport

Handler = Callable[[Any], Any]


class RuntimeBus:
    """Generic message bus.

    Knows only one thing: message type → handler.
    No resolver, no transport, no registry — just routing.
    """

    def __init__(self) -> None:
        self._handlers: dict[type, Handler] = {}
        self.transport: DirectTransport
        self.resolver: Resolver

    def register(self, message_type: type, handler: Handler) -> None:
        self._handlers[message_type] = handler

    def dispatch(self, message: Any) -> Any:
        handler = self._handlers.get(type(message))
        if handler is None:
            raise KeyError(f"no handler for {type(message).__name__}")
        return handler(message)


_default_bus: RuntimeBus | None = None


def _make_default_bus() -> RuntimeBus:
    from .handlers import (
        CallHandler,
        RegisterProviderHandler,
        UnregisterProviderHandler,
    )

    bus = RuntimeBus()
    resolver = Resolver()
    transport = DirectTransport()

    bus.register(Call, CallHandler(resolver, transport))
    bus.register(RegisterProvider, RegisterProviderHandler(resolver, transport))
    bus.register(UnregisterProvider, UnregisterProviderHandler(resolver, transport))

    bus.resolver = resolver
    bus.transport = transport

    return bus


def get_bus() -> RuntimeBus:
    global _default_bus
    if _default_bus is None:
        _default_bus = _make_default_bus()
    return _default_bus


def set_bus(bus: RuntimeBus) -> None:
    global _default_bus
    _default_bus = bus
