from __future__ import annotations

from typing import Protocol, cast

from y5n.base.flow.channel import Scope
from y5n.base.naming import Key
from y5n.base.nodes import Node
from y5n.base.plugins.ports import OnErrorResolve
from y5n.base.projection import Projection
from y5n.base.runtime import Event, InputContext
from y5n.runtime.connections import (
    RuntimeConnection,
    SessionProjectionRouter,
)
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
from y5n.runtime.settings.version import resolve_runtime_info

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
    ) -> Projection:
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

    async def on_start_command(
        *,
        command: str,
        channel: str,
        flow,
        session,
        remote: str | None = None,
    ):
        if remote:
            conn = RuntimeConnection(url=remote)
            await conn.open(on_projection=SessionProjectionRouter(session))
            await conn.dispatch(Event(payload=command))
            session.push_event(Scope.SESSION, channel, Event(payload=None))
            return

        event = Event(payload=command)
        try:
            new_flow = await engine.dispatch(session=session, event=event)
            if new_flow is None:
                session.push_event(Scope.SESSION, channel, Event(payload=None))
                return
            new_flow.out_channel = channel
            scheduler.schedule_flow(new_flow, session)
        except Exception:
            session.push_event(Scope.SESSION, channel, Event(payload=None))
            return

    engine = CommandEngine(
        on_resolve_node=resolver.resolve,
        on_parse_input=parser.parse,
        on_projection=on_projection_send,
        on_start_task=task_runner.start,  # async, signature: command/channel/kwargs/flow/session
        on_start_command=on_start_command,
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

    async def on_task_error(*, flow, session, error):
        await on_error_resolve(node=flow.node, session=session, error=error)

    task_runner.on_error(on_task_error)

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
        platform=platform,
        on_schedule=scheduler.run,
        on_join_bus=bus.join,
        on_create_runner=create_runner,
        on_get_session=session_builder.create,
        on_setup=setup_nodes,
        info=resolve_runtime_info(),
    )


# ----------------------------------
# PORTS
# ----------------------------------


class Oninitialize(Protocol):
    async def __call__(self) -> None: ...


class OnHasPermission(Protocol):
    def __call__(self, *, session: Session, perm_key: str) -> bool: ...


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
        view_params: dict | None = None,
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
