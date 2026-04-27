from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import TYPE_CHECKING

from yakoon.base.plugins.container import ModulePorts
from yakoon.base.plugins.ports import OnProject
from yakoon.base.resources import ResourceRef

from .resolver import resolve_resource
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

    commandsets: Sequence[type[CommandSet]]
    """Command sets exported by this controller."""

    resources: ResourceReferences = ResourceReferences("")
    """Resource references used by classes for projections, output man pages, workflows etc."""

    ports: ModulePorts

    def __init__(self, session: Session, command: type[Command]):
        self.session = session
        self.command = command

    @abstractmethod
    def create_command(
        self,
    ) -> Command: ...

    async def project(self, name: str, state: dict | None = None):

        path = resolve_resource(
            i18n_root=self.resources.contracts,
            lang=self.session.lang,
            cmd_key=self.command.key,
        )
        resource = ResourceRef(
            self.resources.package,
            path,
        ).child(name)
        on_project = self.ports.on_get_port(OnProject)

        return await on_project(resource=resource, state=state)

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
