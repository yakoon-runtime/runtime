from __future__ import annotations

import asyncio
import json
from typing import Protocol

from y5n.base.runtime import InputEvent
from y5n.runtime.flow import Flow
from y5n.runtime.runtime import Session


class TaskRunner:

    _on_complete: OnTaskCompleted

    def on_complete(self, on_complete: OnTaskCompleted):
        self._on_complete = on_complete

    def start(self, *, task, flow: Flow, session: Session):
        asyncio.create_task(self._run(task, flow, session))

    async def _run(self, task, flow: Flow, session: Session):
        try:
            cmd = task.command
            kwargs = task.kwargs

            if cmd == "sleep":
                await asyncio.sleep(kwargs.get("seconds", 1))
                result = {"returncode": 0, "stdout": "done", "stderr": ""}
            else:
                args = kwargs.get("args", [])
                cwd = kwargs.get("cwd", None)
                proc = await asyncio.create_subprocess_exec(
                    cmd,
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

            event = InputEvent(data=json.dumps(result), tokens=[], payload=result)
            flow.push_event(event, channel=task.channel)
            self._on_complete(flow=flow, session=session)

        except Exception as e:
            event = InputEvent(data=f"error: {e}", tokens=[], payload={"error": str(e)})
            flow.push_event(event, channel=task.channel)
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
