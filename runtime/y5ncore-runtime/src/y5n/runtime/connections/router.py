from __future__ import annotations

from y5n.base.projection.transfer import ProjectionEvent
from y5n.runtime.runtime import Session


class SessionProjectionRouter:
    """Routes remote projections into a local Session.

    Makes the projection callback explicit instead of
    passing session.emit as a raw callable.
    """

    def __init__(self, session: Session):
        self._session = session

    async def __call__(self, event: object) -> None:
        if isinstance(event, ProjectionEvent):
            await self._session.emit(event)
