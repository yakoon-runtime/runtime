from __future__ import annotations

from yakoon.base.resources.resource import ResourceRef
from yakoon.base.runtime.services import ServiceDirectory
from yakoon.platform.runtime.sessions import Session

from .presenter import DefaultPresenter


class DefaultPresenterService:
    """
    Default factory for session-bound presenters.
    """

    def __init__(self, services: ServiceDirectory) -> None:
        self._services = services

    async def create_presenter(
        self,
        resource: ResourceRef,
        session: Session,
    ) -> DefaultPresenter:
        return DefaultPresenter(
            resource=resource,
            session=session,
            services=self._services,
        )
