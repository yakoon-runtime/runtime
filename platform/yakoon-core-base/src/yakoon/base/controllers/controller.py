from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import TYPE_CHECKING

from yakoon.base.runtime import Container

from .resources import ResourceReferences

if TYPE_CHECKING:
    from yakoon.base.commands import Command, CommandSet, Request
    from yakoon.base.runtime.sessions import Session


class Controller(ABC):
    """Abstract base class for controllers.

    A controller is the composition root for a "program context" in the engine:
      - it provides services via a Container
      - it defines available commands via CommandSets
      - it provides template and workflow sources
      - it exposes lifecycle hooks around resolution and execution

    Public API contract:
      - `commandsets` is the authoritative way to expose commands for registration.
      - `services` is injected at runtime (platform responsibility).
      - Hooks must be side-effect safe and should not assume a command exists unless
        their signature includes one.

    Notes:
        Keep controllers lightweight. Business logic belongs in services and commands.
    """

    id: str = "unnamed"
    """Unique controller identifier used for command prefix resolution."""

    is_shell: bool = False
    """If True, the controller acts as a shell-like environment."""

    is_listed: bool = True
    """If False, the controller is hidden from listings (e.g. man/help, UI menus)."""

    is_activatable: bool = True
    """If False, the controller cannot be activated as an interactive context."""

    resources: ResourceReferences = ResourceReferences("")
    """Resource references used by classes for projections, output man pages, workflows etc."""

    def __init__(self) -> None:
        """Initialize a controller with an empty service directory.

        The platform is expected to inject a fully configured directory via
        `connect_services()` before command execution.
        """
        self.container: Container | None = None

    @property
    @abstractmethod
    def commandsets(self) -> Sequence[type[CommandSet]]:
        """Command sets exposed by this controller.

        Returns:
            A sequence of CommandSet types. Registries iterate these sets and register
            their `commands()` into the command catalog for this controller.

        Notes:
            Prefer returning *types* (not instances) for determinism and cheaper wiring.
        """
        raise NotImplementedError

    def set_container(self, container: Container) -> None:
        """Inject the container.

        Args:
            container: The fully configured container provided by the platform.
        """
        self.container = container

    async def on_before_resolve(self, session: Session) -> None:
        """Hook executed before command resolution.

        Intended use:
            - register dynamic commands for the current session
            - add context-sensitive aliases or shortcuts
            - adjust builtins for a specific program state

        This hook runs regardless of whether a valid command is found later.
        """
        return None

    async def on_before_run_command(
        self, session: Session, request: Request, command: Command
    ) -> None:
        """Hook executed immediately before a command is run.

        Intended use:
            - enforce permissions
            - inject command context (batch id, controller id, tenant)
            - audit/tracing

        Args:
            session: Current runtime session.
            request: Parsed request that produced this command.
            command: The resolved command about to execute.
        """
        return None

    async def on_after_run_command(
        self, session: Session, request: Request, command: Command
    ) -> None:
        """Hook executed immediately after a command finished.

        Intended use:
            - cleanup after a command
            - logging/audit
            - update controller-local state

        Args:
            session: Current runtime session.
            request: Parsed request that produced this command.
            command: The command that just executed.
        """
        return None

    async def on_cleanup(self, session: Session) -> None:
        """Hook executed after a command cycle, even if exceptions occurred.

        Intended use:
            - remove dynamic command groups
            - reset temporary state
            - undo session tweaks

        Args:
            session: Current runtime session.
        """
        return None
