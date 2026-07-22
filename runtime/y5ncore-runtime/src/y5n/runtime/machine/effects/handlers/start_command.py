from typing import cast

from y5n.runtime.api.flow.primitives import Effect, StartCommand
from y5n.runtime.flow import Flow
from y5n.runtime.runtime import Session


class StartCommandHandler:
    """Handles StartCommand: dispatches a runtime command as a sub-flow.

    The sub-flow's projection output is redirected to the configured
    channel.  Supports optional remote execution via the effect's
    remote field.
    """

    def __init__(self, on_start_command):
        self._on_start_command = on_start_command

    async def execute(self, effect: Effect, session: Session, flow: Flow) -> None:
        e = cast(StartCommand, effect)
        await self._on_start_command(
            command=e.command,
            channel=e.channel,
            flow=flow,
            session=session,
            remote=e.remote,
        )
