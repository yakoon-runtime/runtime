from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from yakoon.base.capabilities.presenters import (
    Presenter,
    PresenterService,
)
from yakoon.base.controllers import resolve_resource
from yakoon.base.naming import NamespaceService

from .operations import Operations
from .types import (
    CommandKind,
    CommandScope,
    CommandVisibility,
)

if TYPE_CHECKING:

    from yakoon.base.naming import Namespace
    from yakoon.base.runtime.services import ServiceDirectory

    from .context import CommandContext
    from .request import Request


class WorkflowContextRequired(RuntimeError):
    """Raised when a workflow-only command is invoked without a workflow batch."""


class Command(ABC):
    """Base class for all executable commands."""

    # Public identity
    key: str

    # Execution metadata
    kind: CommandKind = CommandKind.USER
    scope: CommandScope = CommandScope.CONTROLLER
    visibility: CommandVisibility = CommandVisibility.NORMAL

    # If True, dispatcher or command must enforce workflow context.
    requires_workflow: bool = False

    # Runtime-provided
    ctx: CommandContext

    @property
    def services(self) -> ServiceDirectory:
        """Service directory exposed by the active controller."""
        if not self.ctx:
            raise RuntimeError("Context cannot be None")
        if not self.ctx.controller:
            raise RuntimeError("Context controller cannot be None")
        if not self.ctx.controller.services:
            raise RuntimeError("Controller services cannot be None")
        return self.ctx.controller.services

    @property
    def op(self):
        if not hasattr(self, "_op"):
            self._op = Operations(self)
        return self._op

    async def get_namespace(self, kind: str, space: str | None) -> Namespace:
        """Resolve the namespace for the current session."""
        namespaces = self.services.get(NamespaceService)
        return await namespaces.from_session(self.ctx.session, kind, space)

    async def get_presenter(self) -> Presenter:
        if not self.ctx:
            raise RuntimeError("Context cannot be None")
        if not self.ctx.controller:
            raise RuntimeError("Context controller cannot be None")
        controller = self.ctx.controller
        presenter_service = self.services.get(PresenterService)

        resources = controller.resources
        if not resources.contracts:
            raise RuntimeError("Controller has no contracts root defined.")

        session = self.ctx.session
        ref = resolve_resource(
            resources,
            i18n_root=resources.contracts,
            lang=session.lang,
            key=self.key,
        )

        return await presenter_service.create_presenter(ref, session)

    @abstractmethod
    def run(self, request: Request):
        raise NotImplementedError
