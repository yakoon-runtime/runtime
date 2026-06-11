from __future__ import annotations

import asyncio
from collections.abc import Mapping
from typing import Protocol

from y5n.base.flow.channel import Scope
from y5n.base.runtime import Event
from y5n.runtime.flow import Flow
from y5n.runtime.runtime import Session


class TaskRunner:

    _on_complete: OnTaskCompleted
    _on_error: OnTaskError

    def on_complete(self, on_complete: OnTaskCompleted):
        self._on_complete = on_complete

    def on_error(self, on_error: OnTaskError):
        self._on_error = on_error

    async def start(self, *, command: str, channel: str, scope: Scope, kwargs: Mapping, flow: Flow, session: Session) -> None:
        asyncio.create_task(self._run(command, channel, scope, kwargs, flow, session))

    async def _run(self, command: str, channel: str, scope: Scope, kwargs: Mapping, flow: Flow, session: Session) -> None:
        try:
            try:
                args = kwargs.get("args", [])
                cwd = kwargs.get("cwd", None)
                proc = await asyncio.create_subprocess_exec(
                    command,
                    *args,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=cwd,
                )
                stdout, stderr = await proc.communicate()
                result = {
                    "returncode": proc.returncode,
                    "stdout": stdout.decode(errors="replace"),
                    "stderr": stderr.decode(errors="replace"),
                }
            except Exception as e:
                result = {"error": str(e)}

            session.push_event(scope, channel, Event(payload=result))
            self._on_complete(flow=flow, session=session)
        except Exception as e:
            await self._on_error(flow=flow, session=session, error=e)


# ----------------------------------
# PORTS
# ----------------------------------


class OnTaskCompleted(Protocol):
    def __call__(
        self,
        *,
        flow: Flow,
        session: Session,
    ) -> None: ...


class OnTaskError(Protocol):
    async def __call__(
        self,
        *,
        flow: Flow,
        session: Session,
        error: Exception,
    ) -> None: ...
