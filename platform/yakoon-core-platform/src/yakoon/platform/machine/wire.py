from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Protocol, cast

from yakoon.base.naming import Key
from yakoon.base.nodes import Node
from yakoon.base.projection import Projection
from yakoon.base.resources import ResourceRef
from yakoon.base.runtime import InputContext
from yakoon.platform.runtime import Session
from yakoon.platform.runtime.bus import BusOutput, SessionBus

from .engine import CommandEngine
from .host import RuntimeHost
from .parser import InputParser
from .resolver import InvocationResolver
from .runner import Runner
from .scheduler import Scheduler
from .session import SessionBuilder


def build_machine(
    nodes: Sequence[Node],
    on_suggest: OnSuggest,
    on_projection: OnProjection,
    on_session: OnGetOrCreateSession,
    on_has_permission: OnHasPermission,
    on_audit_log: OnAuditLog,
    on_audit_error: OnAuditError,
    on_audit_warning: OnAuditWarning,
    on_audit_security: OnAuditSecurity,
    on_load_projection: OnLoadProjection,
    on_initialize: Oninitialize,
) -> RuntimeHost:

    # ---------------
    # --- ROUTING ---
    # ---------------

    resolver = InvocationResolver(
        nodes=nodes,
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
        on_projection=on_projection,
        on_audit_security=on_audit_security,
    )

    def get_resource(key: str, lang: str, state: dict[str, Any] | None) -> ResourceRef:
        root = nodes[0].root
        return root.get_resource(key, lang=lang)

    # -----------------
    # --- EXECUTION ---
    # -----------------

    scheduler = Scheduler(
        on_setup=engine.setup,
        on_dispatch=engine.dispatch,
        on_step_flow=engine.step_flow,
        on_show_projection=on_projection,
        on_audit_error=on_audit_error,
        on_audit_warning=on_audit_warning,
        on_get_projection=on_load_projection,
        on_get_resource=get_resource,
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

        for node in nodes:
            node.walk(collect_nodes)
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


class OnProjection(Protocol):
    async def __call__(
        self,
        *,
        session: Session,
        projection: Projection,
        ctx: InputContext | None,
        job_id: str = "system",
    ) -> None: ...


class OnSuggest(Protocol):
    def __call__(
        self,
        *,
        value: str,
        choices: list[str],
        limit: int = 3,
        cutoff: float = 0.5,
    ) -> list[str]: ...


class OnLoadProjection(Protocol):
    async def __call__(
        self,
        *,
        resource: ResourceRef,
        state: dict[str, Any] | None = None,
    ) -> Projection: ...
