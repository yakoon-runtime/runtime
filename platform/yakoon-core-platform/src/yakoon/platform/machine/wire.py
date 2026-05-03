from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, cast

from yakoon.base.application.application import Application
from yakoon.base.commands.command import Command
from yakoon.base.controllers.controller import Controller
from yakoon.base.naming import Key
from yakoon.base.projection.model.model import Projection
from yakoon.base.runtime.input.context import InputContext
from yakoon.platform.runtime import Session
from yakoon.platform.runtime.bus import BusOutput, SessionBus

from .engine import CommandEngine
from .host import RuntimeHost
from .parser import InputParser
from .resolver import CommandResolver
from .runner import Runner
from .scheduler import Scheduler
from .session import SessionBuilder


def build_machine(
    applications: Sequence[Application],
    on_projection: OnProjection,
    on_session: OnGetOrCreateSession,
    on_authorize: OnHasPermission,
    on_bootstrap_permissions: OnBootstrapPermissions,
    on_audit_log: OnAuditLog,
    on_audit_error: OnAuditError,
    on_audit_warning: OnAuditWarning,
    on_audit_security: OnAuditSecurity,
) -> RuntimeHost:

    # --- ROUTING ---

    resolver = CommandResolver(
        applications=applications,
    )

    # --- FACTORY ---

    def create_command(
        app: Application,
        session: Session,
        controller: type[Controller],
        command: type[Command],
    ) -> Command:

        return app.create_command(
            controller=controller,
            command=command,
            session=session,
        )

    # --- PARSING ---

    parser = InputParser()

    # --- ORCHESTRATION ---

    engine = CommandEngine(
        on_match_command=resolver.resolve,
        on_parse_input=parser.parse,
        on_authorize=on_authorize,
        on_projection=on_projection,
        on_create_command=create_command,
        on_audit_security=on_audit_security,
    )

    # --- EXECUTION ---

    scheduler = Scheduler(
        on_dispatch=engine.dispatch,
        on_step_flow=engine.step_flow,
        on_projection=on_projection,
        on_audit_error=on_audit_error,
        on_audit_warning=on_audit_warning,
    )

    # --- SESSION HANDLING ---

    bus = SessionBus()

    async def get_session(key: Key) -> Session:
        session, _ = await on_session(key=key)
        psession = cast(Session, session)
        psession.bind_io(BusOutput(bus))
        return psession

    session_builder = SessionBuilder(
        on_get_session=get_session,
        on_apply_permissions=on_bootstrap_permissions,
    )

    # --- SESSION EXECUTION ---

    def create_runner(session: Session) -> Runner:
        runner = Runner(
            session=session,
            global_commands=resolver.globals(),
            on_dispatch=scheduler.dispatch,
            on_schedule_flow=scheduler.schedule_flow,
        )
        return runner

    # --- LIFECYCLE ---

    async def on_start():
        for a in applications:
            await a.start()

    # --- HOSTING ---

    return RuntimeHost(
        on_schedule=scheduler.run,
        on_join_bus=bus.join,
        on_create_runner=create_runner,
        on_get_session=session_builder.create,
        on_initialize=on_start,
    )


# ----------------------------------
# PORTS
# ----------------------------------


class OnHasPermission(Protocol):
    def __call__(self, *, session: Session, perm_key: str) -> bool: ...


class OnBootstrapPermissions(Protocol):
    def __call__(self, *, session: Session): ...


class OnAuditError(Protocol):
    def __call__(self, *, exc: Exception, session: Session) -> None: ...


class OnAuditLog(Protocol):
    def __call__(self, *, message: str) -> None: ...


class OnAuditSecurity(Protocol):
    def __call__(self, *, session, obj, action) -> None: ...


class OnAuditWarning(Protocol):
    def __call__(self, *, message: str, session: Session) -> None: ...


class OnGetOrCreateSession(Protocol):
    async def __call__(self, key: Key, **kwargs) -> tuple[Session, bool]: ...


class OnProjection(Protocol):
    async def __call__(
        self,
        *,
        session: Session,
        projection: Projection,
        ctx: InputContext | None,
        job_id: str = "system",
    ) -> None: ...
