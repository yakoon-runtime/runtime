from y5n.base.flow.primitives import Effect
from y5n.runtime.flow import Flow
from y5n.runtime.runtime import Session


class BackgroundHandler:
    """Handles Background: removes the foreground flow.

    The previously foreground flow continues to run but no longer
    captures user input.
    """

    async def execute(self, effect: Effect, session: Session, flow: Flow) -> None:
        session.set_foreground_flow(None)
