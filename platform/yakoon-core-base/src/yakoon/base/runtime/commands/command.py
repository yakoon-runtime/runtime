from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator, Coroutine
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, TypeAlias

from yakoon.base.capabilities.presenters import (
    Presenter,
    PresenterService,
)
from yakoon.base.ids import NamespaceService
from yakoon.base.runtime.controllers import resolve_resource

from .steps.step import Step
from .types import (
    CommandKind,
    CommandScope,
    CommandVisibility,
)

if TYPE_CHECKING:

    from yakoon.base.runtime.controllers import Controller
    from yakoon.base.runtime.services import ServiceDirectory
    from yakoon.base.runtime.sessions import Session
    from yakoon.base.values import Namespace

    from .request import Request


CommandFlow: TypeAlias = AsyncGenerator[Step, Any]
CommandRun: TypeAlias = Coroutine[Any, Any, CommandFlow]


class WorkflowContextRequired(RuntimeError):
    """Raised when a workflow-only command is invoked without a workflow batch."""


@dataclass(frozen=True, slots=True)
class CommandContext:
    """Runtime context for command execution.

    Attributes:
        controller: Active controller providing services and template configuration.
        batch_id: Workflow batch identifier, if the command is executed within a workflow.
    """

    controller: Controller
    batch_id: str | None = None

    @property
    def is_batch(self) -> bool:
        """True if the command executes within a workflow batch."""
        return self.batch_id is not None


class Command(ABC):
    """Base class for all executable commands.

    Subclasses define the command's identity via class attributes and implement `run()`.

    Public API contract:
        - Commands are cheap to instantiate and should remain stateless.
        - All dependencies are resolved via `context.controller.services`.
        - `run()` returns a `CommandResult` (never raw strings / ad-hoc dicts).

    Required class attributes:
        key: Unique command identifier (often namespaced).
    """

    # Public identity
    key: str

    # Execution metadata
    kind: CommandKind = CommandKind.USER
    scope: CommandScope = CommandScope.CONTROLLER
    visibility: CommandVisibility = CommandVisibility.NORMAL

    # If True, dispatcher or command must enforce workflow context.
    requires_workflow: bool = False

    # Runtime-provided
    context: CommandContext | None = None

    @property
    def services(self) -> ServiceDirectory:
        """Service directory exposed by the active controller."""
        if not self.context:
            raise RuntimeError("Context cannot be None")
        if not self.context.controller:
            raise RuntimeError("Context controller cannot be None")
        if not self.context.controller.services:
            raise RuntimeError("Controller services cannot be None")
        return self.context.controller.services

    def ensure_workflow_context(self) -> str:
        """Return the workflow batch id or raise if missing.

        Returns:
            The workflow batch id.

        Raises:
            WorkflowContextRequired: If the command requires workflow context but none exists.
        """
        if not self.context:
            raise RuntimeError("runtime context was not set.")
        if not self.context.is_batch:
            raise WorkflowContextRequired(
                f"Command '{self.key}' requires a workflow batch context."
            )
        # mypy: batch_id is Optional[str], but context.is_batch guarantees it exists
        return self.context.batch_id  # type: ignore[return-value]

    async def get_namespace(
        self, session: Session, kind: str, space: str | None
    ) -> Namespace:
        """Resolve the namespace for the current session."""
        namespaces = self.services.get(NamespaceService)
        return await namespaces.from_session(session, kind, space)

    async def get_presenter(self, session: Session) -> Presenter:
        if not self.context:
            raise RuntimeError("Context cannot be None")
        if not self.context.controller:
            raise RuntimeError("Context controller cannot be None")
        controller = self.context.controller
        presenter_service = self.services.get(PresenterService)

        resources = controller.resources
        if not resources.contracts:
            raise RuntimeError("Controller has no contracts root defined.")

        ref = resolve_resource(
            resources,
            i18n_root=resources.contracts,
            lang=session.lang,
            key=self.key,
        )

        return await presenter_service.create_presenter(ref, session)

    @abstractmethod
    def run(
        self,
        session: Session,
        request: Request,
    ) -> CommandFlow:
        """Execute the command as an async generator.

        Yields:
            Step: Next step to execute.

        Receives:
            Arbitrary data from step results via `yield`.

        Notes:
            - Do not use return values; data flows via `yield`.
            - Reserve exceptions for programmer errors.
        """
        raise NotImplementedError
