from typing import cast

from y5n.runtime.api.flow.primitives import CwdEffect, Effect
from y5n.runtime.engine.flow import Flow
from y5n.runtime.engine.runtime import Session


class CwdHandler:
    """Handles CwdEffect: changes the session's working directory."""

    async def execute(self, effect: Effect, session: Session, flow: Flow) -> None:
        e = cast(CwdEffect, effect)
        session.set_cwd(e.path)
