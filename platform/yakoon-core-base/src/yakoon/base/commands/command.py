from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from yakoon.base.capabilities.interaction import FieldPolicyEngine
from yakoon.base.controllers import resolve_resource
from yakoon.base.naming import NamespaceResolver
from yakoon.base.projection import (
    Projector,
    ProjectorFactory,
)

from .types import (
    CommandKind,
    CommandScope,
    CommandVisibility,
)

if TYPE_CHECKING:

    from yakoon.base.naming import Namespace
    from yakoon.base.runtime import Container

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
    scope: CommandScope = CommandScope.APP
    visibility: CommandVisibility = CommandVisibility.NORMAL

    # If True, dispatcher or command must enforce workflow context.
    requires_workflow: bool = False

    # Runtime-provided
    ctx: CommandContext

    @property
    def policies(self) -> FieldPolicyEngine:
        return self.container.get(FieldPolicyEngine)

    @property
    def container(self) -> Container:
        """Container exposed by the active controller."""
        if not self.ctx:
            raise RuntimeError("Context cannot be None")
        if not self.ctx.controller:
            raise RuntimeError("Context controller cannot be None")
        if not self.ctx.controller.container:
            raise RuntimeError("Controller services cannot be None")
        return self.ctx.controller.container

    async def get_namespace(self, kind: str, space: str | None) -> Namespace:
        """Resolve the namespace for the current session."""
        namespaces = self.container.get(NamespaceResolver)
        return await namespaces.from_session(self.ctx.session, kind, space)

    async def create_projector(self) -> Projector:
        if not self.ctx:
            raise RuntimeError("Context cannot be None")
        if not self.ctx.controller:
            raise RuntimeError("Context controller cannot be None")

        controller = self.ctx.controller
        projector_service = self.container.get(ProjectorFactory)

        resources = controller.resources
        if not resources.contracts:
            raise RuntimeError("Controller has no contracts root defined")

        session = self.ctx.session
        ref_contract = resolve_resource(
            resources,
            i18n_root=resources.contracts,
            lang=session.lang,
            key=self.key,
        )

        ref_asset = resolve_resource(
            resources,
            i18n_root=resources.assets,
            lang=session.lang,
            key=self.key,
        )

        return await projector_service.create(ref_contract, ref_asset, session)

    @abstractmethod
    def run(self, request: Request):
        raise NotImplementedError
