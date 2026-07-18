from __future__ import annotations

from typing import Protocol, cast

from y5n.base.flow import Scope
from y5n.base.naming import Key
from y5n.base.nodes import Node
from y5n.base.ports.protocols import OnErrorResolve
from y5n.base.runtime import Event, InputContext
from y5n.base.runtime.input import Origin
from y5n.runtime.connections import (
    RuntimeConnection,
    SessionDocumentRouter,
)
from y5n.runtime.flow import Flow
from y5n.runtime.interaction import Interactor
from y5n.runtime.machine import (
    CommandEngine,
    EffectExecutor,
    InputParser,
    InvocationResolver,
    OnGetNode,
    Runner,
    RuntimeHost,
    Scheduler,
    SessionBuilder,
    TaskRunner,
)
from y5n.runtime.runtime import Session
from y5n.runtime.runtime.bus import BusOutput
from y5n.runtime.settings import Settings
from y5n.runtime.settings.version import resolve_runtime_info

# ----------------------------------
# ERRORS
# ----------------------------------


def build_machine(
    platform: Node,
    on_suggest: OnSuggest,
    on_projection_send: OnDocumentSend,
    on_session: OnGetOrCreateSession,
    on_has_permission: OnHasPermission,
    on_audit_warning: OnAuditWarning,
    on_initialize: Oninitialize,
    known_runtimes: dict[str, str],
    settings: Settings,
    on_get_node: OnGetNode,
) -> RuntimeHost:

    # ---------------
    # --- ROUTING ---
    # ---------------

    resolver = InvocationResolver(
        root=platform,
        on_authorize=on_has_permission,
        on_suggest=on_suggest,
        on_get_node=on_get_node,
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
    ) -> dict:
        try:
            on_error = node.ports.get(OnErrorResolve)
            return await on_error(key=node.path, session=session, error=error)
        except Exception as exc:  # fallback
            print(exc)
            on_error = node.root.ports.get(OnErrorResolve)
            return await on_error(key=node.path, session=session, error=error)

    # ---------------
    # --- TASKS  ----
    # ---------------

    task_runner = TaskRunner()

    # ------------------
    # --- INTERACTOR ---
    # ------------------

    interactor = Interactor()

    # -----------------------
    # --- START COMMAND  ----
    # -----------------------

    async def on_start_command(
        *,
        command: str,
        channel: str,
        flow,
        session,
        remote: str | None = None,
    ):
        if remote:
            conn = RuntimeConnection(url=host.resolve_runtime(remote))

            async def on_remote_done():
                session.push_event(Scope.SESSION, channel, Event(payload=None))
                # Transport cleanup is handled by the receive-loop finally block.
                # We do NOT call conn.close() here because we are inside the
                # transport's own receive-loop task.

            await conn.open(on_projection=SessionDocumentRouter(session))
            conn.set_on_done(on_remote_done)
            await conn.dispatch(Event(payload=command))
            return

        event = Event(payload=command, context=InputContext(origin=Origin.SCHEDULER))
        try:
            new_flow = await engine.dispatch(session=session, event=event)
            if new_flow is None:
                # No flow was created (command not found / not executable).
                # The scheduler will never push a completion event,
                # so we must unblock the waiting caller ourselves.
                session.push_event(Scope.SESSION, channel, Event(payload=None))
                return
            new_flow.out_channel = channel
            scheduler.schedule_flow(new_flow, session)
        except Exception:
            # An exception during dispatch means no flow was scheduled.
            # The scheduler will not push completion — unblock the caller.
            session.push_event(Scope.SESSION, channel, Event(payload=None))
            return

    # ----------------
    # --- EFFECTS ----
    # ----------------

    effect_executor = EffectExecutor(
        on_projection=on_projection_send,
        on_start_task=task_runner.start,
        on_start_command=on_start_command,
    )

    # ---------------
    # --- ENGINE ----
    # ---------------

    engine = CommandEngine(
        on_resolve_node=resolver.resolve,
        on_parse_input=parser.parse,
        on_intercept=interactor.intercept,
        on_apply_effects=effect_executor.execute,
    )

    # -----------------
    # --- SCHEDULER ---
    # -----------------

    async def flow_complete(flow: Flow, session: Session) -> None:
        await host.flow_complete(flow, session)

    scheduler = Scheduler(
        platform=platform,
        on_setup=engine.setup,
        on_dispatch=engine.dispatch,
        on_step_flow=engine.step_flow,
        on_show_projection=on_projection_send,
        on_audit_warning=on_audit_warning,
        on_error_resolve=on_error_resolve,
        on_flow_complete=flow_complete,
    )

    # -------------------------
    # --- ON TASK COMPLETED ---
    # -------------------------

    async def on_task_error(*, flow, session, error):
        await on_error_resolve(node=flow.node, session=session, error=error)

    task_runner.on_error(on_task_error)
    task_runner.on_complete(scheduler.schedule_flow)

    # ------------------------
    # --- SESSION HANDLING ---
    # ------------------------

    async def get_session(key: Key) -> Session:
        session, _ = await on_session(key=key)
        psession = cast(Session, session)
        psession.bind_io(BusOutput(psession._bus))
        if not psession.get_data("fs:root"):
            psession.set_data("fs:root", settings.runtime.workspace_path)
            psession.set_cwd("/")
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

    host = RuntimeHost(
        on_schedule=scheduler.run,
        on_create_runner=create_runner,
        on_get_session=session_builder.create,
        on_setup=setup_nodes,
        known_runtimes=known_runtimes,
        info=resolve_runtime_info(),
    )

    return host


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


class OnDocumentSend(Protocol):
    async def __call__(
        self,
        *,
        session: Session,
        document: dict,
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
