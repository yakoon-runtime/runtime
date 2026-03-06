import time

from yakoon.base.runtime import Command, Request, Session
from yakoon.base.runtime.commands import CommandKind, CommandVisibility
from yakoon.base.runtime.sessions.views import v_text


class CmdSpeedTest(Command):

    key = "speed-test"

    _counter: int = 0
    _start_time: float = time.perf_counter()

    kind = CommandKind.BUILTIN
    visibility = CommandVisibility.DEVELOPER

    async def run(self, session: Session, request: Request) -> None:  # noqa: ARG002

        CmdSpeedTest._counter += 1

        now = time.perf_counter()
        elapsed = now - CmdSpeedTest._start_time
        per_sec = CmdSpeedTest._counter / elapsed if elapsed > 0 else 0.0
        msg = (
            f"count={CmdSpeedTest._counter} | "
            f"elapsed={elapsed:.3f}s | "
            f"rate={per_sec:.2f}/sec"
        )
        # if CmdTest._counter % 1000 == 0:
        await session.emit(v_text(msg))
