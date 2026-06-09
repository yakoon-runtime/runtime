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

    def on_complete(self, on_complete: OnTaskCompleted):
        self._on_complete = on_complete

    async def start(self, *, command: str, channel: str, kwargs: Mapping, flow: Flow, session: Session) -> None:
        asyncio.create_task(self._run(command, channel, kwargs, flow, session))

    async def _run(self, command: str, channel: str, kwargs: Mapping, flow: Flow, session: Session) -> None:
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

        session.push_event(Scope.SESSION, channel, Event(payload=result))
        self._on_complete(flow=flow, session=session)


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
