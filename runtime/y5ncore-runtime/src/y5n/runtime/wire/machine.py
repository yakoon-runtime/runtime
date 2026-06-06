from __future__ import annotations

from typing import Protocol, cast

from y5n.base.naming import Key
from y5n.base.nodes import Node
from y5n.base.plugins.ports import OnErrorResolve
from y5n.base.projection import Projection
from y5n.base.runtime import InputContext
from y5n.runtime.machine import (
    CommandEngine,
    InputParser,
    InvocationResolver,
    Runner,
    RuntimeHost,
    Scheduler,
    SessionBuilder,
    TaskRunner,
)
from y5n.runtime.runtime import Session
from y5n.runtime.runtime.bus import BusOutput, SessionBus

# ----------------------------------
# ERRORS
# ----------------------------------


def build_machine(
    platform: Node,
    on_suggest: OnSuggest,
    on_projection_send: OnProjectionSend,
    on_session: OnGetOrCreateSession,
    on_has_permission: OnHasPermission,
    on_audit_warning: OnAuditWarning,
    on_initialize: Oninitialize,
) -> RuntimeHost:

    # ---------------
    # --- ROUTING ---
    # ---------------

    resolver = InvocationResolver(
        root=platform,
        on_authorize=on_has_permission,
        on_suggest=on_suggest,
    )

    # ---------------
    # --- PARSING ---
    # ---------------

    parser = InputParser()

    # --------------
    # --- ERRORS ---
    # --------------

    async def on_error_resolve(
        *,
        node: Node,
        session,
        error: Exception,
    ) -> Projection | None:
        try:
            on_error = node.ports.get(OnErrorResolve)
            return await on_error(key=node.path, session=session, error=error)
        except Exception:  # fallback
            on_error = node.root.ports.get(OnErrorResolve)
            return await on_error(key=node.path, session=session, error=error)

    # ---------------
    # --- TASKS  ----
    # ---------------

    task_runner = TaskRunner()

    # ----------------
    # --- ENGINE  ----
    # ----------------

    engine = CommandEngine(
        on_resolve_node=resolver.resolve,
        on_parse_input=parser.parse,
        on_projection=on_projection_send,
        on_start_task=task_runner.start,
    )

    # -----------------
    # --- EXECUTION ---
    # -----------------

    scheduler = Scheduler(
        platform=platform,
        on_setup=engine.setup,
        on_dispatch=engine.dispatch,
        on_step_flow=engine.step_flow,
        on_show_projection=on_projection_send,
        on_audit_warning=on_audit_warning,
        on_error_resolve=on_error_resolve,
    )

    # -------------------------
    # --- ON TASK COMPLETED ---
    # -------------------------

    task_runner.on_complete(scheduler.schedule_flow)

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
            runtime_commands={
                ":bg",
            },
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

        platform.walk(collect_nodes)
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
        mode: str = "replace",
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
