from __future__ import annotations

from uuid import uuid4

from yakoon.base import ports
from yakoon.base.models.resource import ResourceRef
from yakoon.base.runtime import Session
from yakoon.base.runtime.services import ServiceDirectory
from yakoon.platform.runtime.render.context import RenderContext

from .inputs import PresenterInputs
from .views import PresenterViews


class Presenter:
    """
    Handles structured, localized output rendering for a command session.

    Wraps the template context and provides high-level methods for emitting
    messages, failures, and notifications using predefined sections in the template.
    """

    def __init__(
        self,
        resource: ResourceRef,
        session: Session,
        services: ServiceDirectory,
    ):
        self._prompts = None
        self._views = None
        self._session = session
        self._services = services
        self._renderer = self._services.get(ports.RendererService)
        self._view_id = f"view.{uuid4().hex}"

        self._ctx = RenderContext(
            resource=resource,
            lang=session.lang,
        )

    @property
    def inputs(self) -> PresenterInputs:
        if not self._prompts:
            self._prompts = PresenterInputs(
                self._ctx, self._session, self._services, self._view_id
            )
        return self._prompts

    @property
    def views(self) -> PresenterViews:
        if not self._views:
            self._views = PresenterViews(
                self._ctx, self._session, self._services, self._view_id
            )
        return self._views
