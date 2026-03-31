from __future__ import annotations

from yakoon.base.resources.resource import ResourceRef
from yakoon.base.runtime import Container
from yakoon.platform.runtime.sessions import Session

from .projector import TemplateProjector


class TemplateProjectorFactory:
    """
    Default factory for session-bound projectors.
    """

    def __init__(self, container: Container) -> None:
        self._container = container

    async def create(
        self,
        resource: ResourceRef,
        session: Session,
    ) -> TemplateProjector:
        return TemplateProjector(
            resource=resource,
            session=session,
            container=self._container,
        )
