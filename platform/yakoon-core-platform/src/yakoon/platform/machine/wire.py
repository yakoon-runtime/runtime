from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, cast

from yakoon.base.application.application import Application
from yakoon.base.commands.command import Command
from yakoon.base.controllers.controller import Controller
from yakoon.base.naming import Key
from yakoon.base.projection.transfer import Output
from yakoon.base.runtime import Container
from yakoon.base.runtime.sessions import SessionStore
from yakoon.platform.catalogs import AppQueryBuilder, CommandQueryBuilder
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
    a_query: AppQueryBuilder,
    c_query: CommandQueryBuilder,
    on_has_exec_permission: OnHasExecPermission,
    on_bootstrap_permissions: OnBootstrapPermissions,
    on_get_applications: OnGetApplications,
    on_audit_log: OnAuditLog,
    on_audit_error: OnAuditError,
    on_audit_warning: OnAuditWarning,
    on_audit_security: OnAuditSecurity,
    container: Container,
):

    output = container.get(Output)
    sessions = container.get(SessionStore)

    # --- Command Resolver ---
    resolver = CommandResolver(
        on_match_command=c_query.for_context,
        on_get_context=on_get_applications,
    )

    # --- create command ---
    def create_command(
        session: Session, controller: type[Controller], command: type[Command]
    ) -> Command:
        app = a_query.get(command.app_id)
        return app.create_command(
            controller=controller,
            command=command,
            lang=session.lang,
        )

    # --- Input Parser ---
    parser = InputParser()

    # --- Command Engine ---
    engine = CommandEngine(
        on_match_command=resolver.resolve,
        on_parse_input=parser.parse,
        on_authorize=on_has_exec_permission,
        on_projection=output.send_projection,
        on_create_command=create_command,
        on_audit_security=on_audit_security,
        on_get_app=a_query.get,
        on_get_shell_app=a_query.shell,
    )

    # --- Scheduler ---
    scheduler = Scheduler(
        on_dispatch=engine.dispatch,
        on_step_flow=engine.step_flow,
        on_projection=output.send_projection,
        on_audit_error=on_audit_error,
        on_audit_warning=on_audit_warning,
    )

    # --- Session Bus & Session handling ---
    bus = SessionBus()

    async def get_session(key: Key) -> Session:
        session, _ = await sessions.get_or_create(key)
        psession = cast(Session, session)
        psession.bind_io(BusOutput(bus))
        return psession

    session_builder = SessionBuilder(
        on_get_session=get_session,
        on_apply_permissions=on_bootstrap_permissions,
    )

    # --- Runner & Runner handling ---
    global_commands = {cmd.key for cmd in c_query.globals()}

    def create_runner(session: Session) -> Runner:
        runner = Runner(
            session=session,
            global_commands=global_commands,
            on_dispatch=scheduler.dispatch,
            on_schedule_flow=scheduler.schedule_flow,
        )
        return runner

    # --- Host ---
    return RuntimeHost(
        on_schedule=scheduler.run,
        on_join_bus=bus.join,
        on_create_runner=create_runner,
        on_get_session=session_builder.create,
    )


# ----------------------------------
# PORTS
# ----------------------------------


class OnGetApplications(Protocol):
    def __call__(self) -> Sequence[Application]: ...


class OnHasExecPermission(Protocol):
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
