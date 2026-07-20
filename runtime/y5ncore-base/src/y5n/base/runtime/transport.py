"""Transport layer — delivers Calls to providers.

The transport is owned by the Executor. It knows how to reach
a provider by provider_id, but knows nothing about ports or methods.

  DirectTransport  →  in-process callables (PythonExecutor)
  PipeTransport    →  subprocess stdin/stdout (ProcessExecutor)
  SocketTransport  →  TCP/WebSocket (RemoteExecutor)
"""

from __future__ import annotations

import asyncio
import inspect

from .context import Call, Response

_main_loop: asyncio.AbstractEventLoop | None = None


def set_main_loop(loop: asyncio.AbstractEventLoop) -> None:
    global _main_loop
    _main_loop = loop


class DirectTransport:
    """In-process transport. Provider callables live in a local dict."""

    def __init__(self) -> None:
        self._providers: dict[str, dict] = {}
        self._adapters: dict[str, object] = {}

    def register_provider(self, provider_id: str, service: dict) -> None:
        self._providers[provider_id] = service

    def unregister_provider(self, provider_id: str) -> None:
        self._providers.pop(provider_id, None)

    def register_adapter(self, port: str, adapter: object) -> None:
        """Register a system adapter that receives the full Call."""
        self._adapters[port] = adapter

    async def send(self, provider_id: str, call: Call) -> Response:
        adapter = self._adapters.get(call.port)
        if adapter is not None:
            return await self._send_adapter(adapter, call)
        service = self._providers.get(provider_id)
        if service is None:
            return Response(error=f"provider '{provider_id}' not found")
        fn = service.get(call.method)
        if fn is None:
            return Response(error=f"method '{call.method}' not found")
        return await self._exec(fn, call.args or {})

    async def _send_adapter(self, adapter: object, call: Call) -> Response:
        fn = getattr(adapter, call.method, None)
        if fn is None:
            return Response(error=f"method '{call.method}' not found")
        return await self._exec(fn, call.args or {}, call)

    async def _exec(self, fn, args: dict, call: Call | None = None) -> Response:
        try:
            if call is not None:
                result = fn(call, **args)
            else:
                result = fn(**args)
            if inspect.iscoroutine(result) or inspect.isawaitable(result):
                result = await result
            return Response(result=result)
        except Exception as e:
            return Response(error=str(e))

    def serve(self) -> None:
        return
