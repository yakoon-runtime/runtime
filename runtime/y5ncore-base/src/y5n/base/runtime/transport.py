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

    def register_provider(self, provider_id: str, service: dict) -> None:
        self._providers[provider_id] = service

    def unregister_provider(self, provider_id: str) -> None:
        self._providers.pop(provider_id, None)

    def send(self, provider_id: str, call: Call) -> Response:
        service = self._providers.get(provider_id)
        if service is None:
            return Response(error=f"provider '{provider_id}' not found")
        fn = service.get(call.method)
        if fn is None:
            return Response(error=f"method '{call.method}' not found")
        args = call.args or {}
        try:
            result = fn(**args)
            if inspect.iscoroutine(result):
                try:
                    loop = asyncio.get_running_loop()
                    result = loop.run_until_complete(result)
                except RuntimeError:
                    if _main_loop is None:
                        return Response(error="no event loop available")
                    future = asyncio.run_coroutine_threadsafe(result, _main_loop)
                    result = future.result()
            return Response(result=result)
        except Exception as e:
            return Response(error=str(e))

    def serve(self) -> None:
        return
