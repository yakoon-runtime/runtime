from typing import cast

from y5n.runtime.api.flow.primitives import Effect, StartTask
from y5n.runtime.flow import Flow
from y5n.runtime.runtime import Session


class StartTaskHandler:
    """Handles StartTask: runs an OS process as a background task.

    The process runs independently and sends its result (returncode,
    stdout, stderr) to the configured channel via the registered
    on_start_task callback.
    """

    def __init__(self, on_start_task):
        self._on_start_task = on_start_task

    async def execute(self, effect: Effect, session: Session, flow: Flow) -> None:
        e = cast(StartTask, effect)
        await self._on_start_task(
            command=e.command,
            channel=e.channel,
            scope=e.scope,
            kwargs=e.kwargs,
            flow=flow,
            session=session,
        )
