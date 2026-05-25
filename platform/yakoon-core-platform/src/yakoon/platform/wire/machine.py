from __future__ import annotations

from typing import Any, Protocol, cast

from yakoon.base.errors import ErrorKey, UnhandledError
from yakoon.base.naming import Key
from yakoon.base.nodes import Node
from yakoon.base.nodes.errors import UnknowOptionsError, UsageError
from yakoon.base.projection import Projection
from yakoon.base.resources import ResourceRef
from yakoon.base.runtime import InputContext
from yakoon.platform.machine import (
    CommandEngine,
    InputParser,
    InvocationResolver,
    Runner,
    RuntimeHost,
    Scheduler,
    SessionBuilder,
)
from yakoon.platform.runtime import NodeNotFound, PermissionDenied, Session
from yakoon.platform.runtime.bus import BusOutput, SessionBus

# ----------------------------------
# ERRORS
# ----------------------------------

errors = {
    UnhandledError: "error.sam",
    NodeNotFound: "command/not_found.sam",
    UsageError: "command/usage.sam",
    UnknowOptionsError: "command/unknown_options.sam",
    PermissionDenied: "permissions/denied.sam",
}


def build_machine(
    root: Node,
    on_suggest: OnSuggest,
    on_projection_send: OnProjectionSend,
    on_projection_create: OnProjectionCreate,
    on_session: OnGetOrCreateSession,
    on_has_permission: OnHasPermission,
    on_audit_log: OnAuditLog,
    on_audit_error: OnAuditError,
    on_audit_warning: OnAuditWarning,
    on_audit_security: OnAuditSecurity,
    on_initialize: Oninitialize,
) -> RuntimeHost:

    # ---------------
    # --- ROUTING ---
    # ---------------

    resolver = InvocationResolver(
        root=root,
        on_authorize=on_has_permission,
        on_suggest=on_suggest,
    )

    # ---------------
    # --- PARSING ---
    # ---------------

    parser = InputParser()

    # ---------------------
    # --- ORCHESTRATION ---
    # ----------------------

    engine = CommandEngine(
        on_resolve_node=resolver.resolve,
        on_parse_input=parser.parse,
        on_projection=on_projection_send,
        on_audit_security=on_audit_security,
    )

    # ------------------------
    # --- PROJECTION ---
    # ------------------------

    async def load_projection(
        *, key: ErrorKey, lang: str, state: dict | None = None
    ) -> Projection:

        parts = errors.get(key)
        resource = ResourceRef(
            package="yakoon.platform",
            path=f"templates/{lang}/{parts}",
        )
        return await on_projection_create(resource=resource, state=state)

    # -----------------
    # --- EXECUTION ---
    # -----------------

    scheduler = Scheduler(
        on_setup=engine.setup,
        on_dispatch=engine.dispatch,
        on_step_flow=engine.step_flow,
        on_show_projection=on_projection_send,
        on_audit_error=on_audit_error,
        on_audit_warning=on_audit_warning,
        on_load_projection=load_projection,
    )

    # ------------------------
    # --- SESSION HANDLING ---
    # ------------------------

    bus = SessionBus()

    async def get_session(key: Key) -> Session:
        session, _ = await on_session(key=key)
        psession = cast(Session, session)
        psession.bind_io(BusOutput(bus))
        return psession

    session_builder = SessionBuilder(
        on_get_session=get_session,
    )

    # -------------------------
    # --- SESSION EXECUTION ---
    # -------------------------

    def create_runner(session: Session) -> Runner:
        runner = Runner(
            session=session,
            global_commands=resolver.globals(),
            on_dispatch=scheduler.dispatch,
            on_schedule_flow=scheduler.schedule_flow,
        )
        return runner

    # -------------------
    # --- SETUP NODES ---
    # -------------------

    async def setup_nodes(session):

        await on_initialize()

        nodes_to_setup: list[Node] = []

        def collect_nodes(node: Node):
            if node.has_setup():
                nodes_to_setup.append(node)

        root.walk(collect_nodes)
        for node in nodes_to_setup:
            await scheduler.setup(session, node)

    # ---------------
    # --- HOSTING ---
    # ---------------

    return RuntimeHost(
        on_schedule=scheduler.run,
        on_join_bus=bus.join,
        on_create_runner=create_runner,
        on_get_session=session_builder.create,
        on_setup=setup_nodes,
    )


# ----------------------------------
# PORTS
# ----------------------------------


class Oninitialize(Protocol):
    async def __call__(self) -> None: ...


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


class OnProjectionSend(Protocol):
    async def __call__(
        self,
        *,
        session: Session,
        projection: Projection,
        ctx: InputContext | None,
        job_id: str = "system",
    ) -> None: ...


class OnProjectionCreate(Protocol):
    async def __call__(
        self,
        *,
        resource: ResourceRef,
        state: dict[str, Any] | None = None,
    ) -> Projection: ...


class OnSuggest(Protocol):
    def __call__(
        self,
        *,
        value: str,
        choices: list[str],
        limit: int = 3,
        cutoff: float = 0.5,
    ) -> list[str]: ...
