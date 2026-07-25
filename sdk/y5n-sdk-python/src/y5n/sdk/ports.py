"""Port access — communicate with runtime services.

Usage:
    from y5n.sdk import ports

    class Greeter:
        def greet(self, name="World"):
            return f"Hello, {name}!"

    ports.promote("hello", Greeter())

    hello = ports.get("hello")
    print(hello.greet(name="Yakoon"))
    print(await hello.greet(name="Yakoon"))
"""

from typing import Any

from .context import current as _current_context
from .libs import transport as _transport
from .libs.models import Call, Register, Response


def _extract_methods(service: object) -> dict[str, Any]:
    return {
        name: getattr(service, name)
        for name in dir(service)
        if not name.startswith("_") and callable(getattr(service, name))
    }


async def _invoke(call: Call) -> Response:
    result = await _transport.invoke(call.to_dict())
    if isinstance(result, dict):
        return Response.from_dict(result)
    return Response(result=result)


def _register(reg: Register, callables: dict[str, Any] | None = None) -> None:
    _transport.register(reg.to_dict(), callables)


async def _do_call(call: Call):
    response = await _invoke(call)
    if response.error:
        raise RuntimeError(response.error)
    return response.result


class _RemoteCall:
    """Awaitable that wraps a port call in an asyncio.Task.

    Yielding a Task instead of awaiting directly prevents Futures
    from third-party libraries (e.g. asyncpg) from leaking through
    drive()'s send() mechanism.
    """

    def __init__(self, port: str, method: str, kwargs: dict) -> None:
        self._port = port
        self._method = method
        self._kwargs = kwargs

    def __await__(self):
        ctx = _current_context()
        call = Call(
            port=self._port,
            method=self._method,
            args=self._kwargs,
            caller_path=ctx.node.get("path", ""),
            caller_session_key=ctx.session.get("key", ""),
        )
        result = yield _do_call(call)
        return result


class _PortProxy:
    def __init__(self, port_name: str):
        self._port = port_name

    def __call__(self, **kwargs):
        return _RemoteCall(self._port, "__call__", kwargs)

    def __getattr__(self, name: str):

        def _call(*args, **kwargs):
            if args:
                raise TypeError(
                    f"Port '{self._port}.{name}()' requires keyword arguments, "
                    f"got {len(args)} positional argument(s). "
                    f"Use: {self._port}.{name}(param=value)"
                )
            return _RemoteCall(self._port, name, kwargs)

        return _call


def provide(name: str, service: object) -> None:
    """Register a service visible only within the current node (self).

    Other commands in the same bundle can ``get()`` it.
    """
    callables = _extract_methods(service)
    if not callables:
        callables = {"__call__": service}
    _register(
        Register(name=name, methods=list(callables), placement="self"),
        callables,
    )


def publish(name: str, service: object) -> None:
    """Register a service visible in the current node and its children.

    Useful for framework services that sub-commands may need.
    """
    callables = _extract_methods(service)
    if not callables:
        callables = {"__call__": service}
    _register(
        Register(name=name, methods=list(callables), placement="parent"),
        callables,
    )


def promote(name: str, service: object) -> None:
    """Register a service visible across the entire platform (root).

    Use this for platform-wide services like ``ident.auth``
    that any command anywhere in the tree can consume via ``get()``.
    """
    callables = _extract_methods(service)
    if not callables:
        callables = {"__call__": service}
    _register(
        Register(name=name, methods=list(callables), placement="root"),
        callables,
    )


def get(name: str):
    return _PortProxy(name)
