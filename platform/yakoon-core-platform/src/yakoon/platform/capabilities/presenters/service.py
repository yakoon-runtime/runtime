from __future__ import annotations

from yakoon.base.models.resource import ResourceRef
from yakoon.base.runtime.services import ServiceDirectory

from .presenter import Presenter


class DefaultPresenterService:

    def __init__(self, services: ServiceDirectory):
        self._services = services

    async def create_presenter(self, resource: ResourceRef, session) -> Presenter:

        return Presenter(
            resource,
            session,
            self._services,
        )
