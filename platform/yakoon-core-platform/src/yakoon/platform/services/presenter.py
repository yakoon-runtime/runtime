from __future__ import annotations

from yakoon.base import ports
from yakoon.base.directories.service import ServiceDirectory
from yakoon.base.models.prompt import PromptResult
from yakoon.base.models.resource import ResourceRef
from yakoon.base.runtime.session import Session
from yakoon.platform.runtime.render.context import RenderContext


class PresenterInputs:

    def __init__(
        self, ctx: RenderContext, session: Session, services: ServiceDirectory
    ):
        self._ctx = ctx
        self._session = session
        self._renderer = services.get(ports.RendererService)
        self._inputs = services.get(ports.InputService)

    async def ask(self, section_key: str, **data) -> PromptResult:
        view = await self._renderer.render_view(self._ctx, section_key, **data)
        await self._session.emit(view)
        return await self._inputs.ask_view(self._session, view)


class PresenterViews:

    def __init__(
        self, ctx: RenderContext, session: Session, services: ServiceDirectory
    ):
        self._ctx = ctx
        self._session = session
        self._renderer = services.get(ports.RendererService)

    async def emit(self, section_key: str, **data) -> None:
        view = await self._renderer.render_view(self._ctx, section_key, **data)
        await self._session.emit(view)


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

        self._ctx = RenderContext(
            resource=resource,
            lang=session.lang,
        )

    @property
    def inputs(self) -> PresenterInputs:
        if not self._prompts:
            self._prompts = PresenterInputs(self._ctx, self._session, self._services)
        return self._prompts

    @property
    def views(self) -> PresenterViews:
        if not self._views:
            self._views = PresenterViews(self._ctx, self._session, self._services)
        return self._views


class PresenterService:

    def __init__(self, services: ServiceDirectory):
        self._services = services

    async def create_presenter(self, resource: ResourceRef, session) -> Presenter:

        return Presenter(
            resource,
            session,
            self._services,
        )
