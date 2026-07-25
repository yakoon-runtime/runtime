from __future__ import annotations

from y5n.runtime.api.document.transfer import DocumentEvent
from y5n.runtime.engine.runtime import Session


class SessionDocumentRouter:
    """Routes remote projections into a local Session.

    Makes the projection callback explicit instead of
    passing session.emit as a raw callable.
    """

    def __init__(self, session: Session):
        self._session = session

    async def __call__(self, event: object) -> None:
        if isinstance(event, DocumentEvent):
            await self._session.emit(event)
