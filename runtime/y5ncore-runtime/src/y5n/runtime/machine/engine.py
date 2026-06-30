from __future__ import annotations

import inspect
from collections.abc import Sequence
from typing import Protocol

from y5n.base.flow.channel import Scope
from y5n.base.flow.primitives import (
    AwaitEvent,
    Background,
    Effect,
    EmitEvent,
    EmitView,
    Foreground,
    Outcome,
    StartCommand,
    StartTask,
    Stop,
)
from y5n.base.nodes import Node, NodePath, NodeSpace, Request
from y5n.base.projection import Projection
from y5n.base.runtime import Event
from y5n.base.runtime.input import InputContext, Interaction
from y5n.runtime.flow import Flow, FlowCursor, FlowKind
from y5n.runtime.interaction import resolve_interaction
from y5n.runtime.runtime import (
    Session,
)


class CommandEngine:
    """Core flow execution engine.

    Steps a flow's async generator, applies effects (emit, start, dispatch),
    and returns the outcome control to the scheduler.
    """

    DEFAULT_FLOW_KIND = FlowKind.USER

    def __init__(
        self,
        on_resolve_node: OnResolveNode,
        on_parse_input: OnParseInput,
        on_projection: OnProjection,
        on_start_task: OnTaskStart,
        on_start_command: OnCommandStart,
        on_intercept: OnIntercept,
    ):
        self.on_resolve_command = on_resolve_node
        self.on_parse_input = on_parse_input
        self.on_projection = on_projection
        self.on_start_task = on_start_task
        self.on_start_command = on_start_command
        self._on_intercept = on_intercept

    # ----------------------------------------------------
    # PUBLIC API
    # ----------------------------------------------------

    async def setup(self, session: Session, node: Node) -> Flow | None:

        # TODO: Wie wollen wir darauf später reagieren?
        if not node.has_setup():
            return

        flow = Flow(
            id=session.next_flow_id(),
            node=node,
            event=Event(payload=node.key),
            cursor=FlowCursor("setup"),
            kind=self.DEFAULT_FLOW_KIND,
        )

        session.add_flow(flow)
        return flow

    async def dispatch(self, session: Session, event: Event) -> Flow | None:

        node: Node | None = None
        cmd, tokens, pipeline_commands = self.on_parse_input(event=event)
        if not cmd:
            return None

        # Determine strictness before resolve — lenient allows
        # the Interceptor to collect missing params via FormRenderer.
        caller = event.context.origin if event.context else None
        policy = resolve_interaction(caller, None, Interaction.INHERIT, session.interaction)
        strict = policy is Interaction.CLI

        # find node
        node, resolved_tokens = self.on_resolve_command(
            parent=session.get_current_node(),
            key=cmd,
            tokens=tokens,
            session=session,
            strict=strict,
        )

        tokens = resolved_tokens

        node, tokens = await self._on_intercept(
            node=node,
            tokens=tokens,
            session=session,
            context=event.context,
        )

        if not node.has_run():
            return None

        flow = Flow(
            id=session.next_flow_id(),
            node=node,
            pipeline=pipeline_commands,
            tokens=tokens,
            event=event.update(payload=node.key),
            cursor=FlowCursor("run"),
            kind=self.DEFAULT_FLOW_KIND,
        )

        session.add_flow(flow)
        return flow

    async def step_flow(self, flow: Flow, session: Session) -> Outcome | None:

        node = flow.node
        cursor = flow.cursor

        try:
            # ----------------------------------
            # 21. NORMAL STEP
            # ----------------------------------
            item = await self._next_step(flow, node, flow.event, session)
            if item is None:
                return None

            if isinstance(item, Event):
                try:
                    item = await cursor.send(item)
                except StopAsyncIteration:
                    cursor.pop()
                    if not cursor.has_stack():
                        return Outcome(control=Stop())
                    return None

            # ----------------------------------
            # 2. SUBGENERATOR (SUBFLOW / CALL)
            # ----------------------------------
            if inspect.isasyncgen(item):
                cursor.push(item)
                return None

            # ----------------------------------
            # 3. OUTCOME direkt
            # ----------------------------------
            if isinstance(item, Outcome):
                outcome = item
            else:
                outcome = await item.run(flow)

            # ----------------------------------
            # 4. PIPELINE
            # ----------------------------------
            if outcome.next_steps:
                flow.pipeline = list(outcome.next_steps) + (flow.pipeline or [])

            # ----------------------------------
            # 5. EFFECTS
            # ----------------------------------
            if outcome.effects:
                await self._apply_effects(outcome.effects, session, flow)

            # ----------------------------------
            # 6. CONTROL (Scheduler übernimmt)
            # ----------------------------------
            if outcome.control is not None:
                return outcome

            # ----------------------------------
            # 7. No outcome → next step later
            # ----------------------------------
            return None

        except StopAsyncIteration:
            # current generator is done
            cursor.pop()

            if not cursor.has_stack():
                return Outcome(control=Stop())

            return None

    # ----------------------------------------------------
    # INTERNAL
    # ----------------------------------------------------

    async def _apply_effects(
        self, effects: Sequence[Effect], session: Session, flow: Flow
    ):

        for effect in effects:

            if isinstance(effect, EmitView):
                if flow.out_channel:
                    session.push_event(
                        Scope.SESSION,
                        flow.out_channel,
                        Event(payload=effect.view),
                    )
                else:
                    ctx = effect.ctx or flow.event.context
                    view = effect.view

                    if effect.persist:
                        flow.view = view

                    job_id = effect.job_id or (
                        f"{flow.id}:{effect.space}" if effect.space else flow.id
                    )

                    await self.on_projection(
                        session=session,
                        projection=view,
                        ctx=ctx,
                        job_id=job_id,
                        mode=effect.mode,
                        view_params=effect.view_params,
                    )

            elif isinstance(effect, Foreground):
                flow_id = effect.flow_id or flow.id
                session.set_foreground_flow(flow_id)

            elif isinstance(effect, Background):
                session.set_foreground_flow(None)

            elif isinstance(effect, EmitEvent):
                session.push_event(
                    effect.scope, effect.channel, effect.event, flow=flow
                )

            elif isinstance(effect, StartTask):
                await self.on_start_task(
                    command=effect.command,
                    channel=effect.channel,
                    scope=effect.scope,
                    kwargs=effect.kwargs,
                    flow=flow,
                    session=session,
                )

            elif isinstance(effect, StartCommand):
                await self.on_start_command(
                    command=effect.command,
                    channel=effect.channel,
                    flow=flow,
                    session=session,
                    remote=effect.remote,
                )

    async def _next_step(
        self,
        flow: Flow,
        node: Node,
        event: Event,
        session: Session,
    ):

        # ----------------------------------
        # Resume: Input / Event
        # ----------------------------------
        if isinstance(flow.control, AwaitEvent):

            channel = flow.control.channel
            scope = flow.control.scope

            next_event = session.pop_event(scope, channel, flow=flow)
            if next_event is None:
                return None

            flow.control = None
            return next_event

        # ----------------------------------
        # NEXT
        # ----------------------------------

        request = Request(
            event.payload,
            flow.tokens,
            None,
            session.lang,
        )

        return await flow.cursor.next(
            node,
            NodeSpace(
                path=node.path,
                request=request,
                session=session,
                ports=node.ports,
                ports_from=node.ports_from,
            ),
        )


# ----------------------------------
# PORTS
# ----------------------------------


class OnTaskStart(Protocol):
    async def __call__(
        self,
        *,
        command: str,
        channel: str,
        scope: Scope,
        kwargs: dict,
        flow: Flow,
        session: Session,
    ) -> None: ...


class OnCommandStart(Protocol):
    async def __call__(
        self,
        *,
        command: str,
        channel: str,
        flow,
        session,
        remote: str | None = None,
    ) -> None: ...


class OnResolveNode(Protocol):
    def __call__(
        self,
        *,
        parent: NodePath,
        key: str,
        tokens: list[str] | None,
        session: Session,
        strict: bool = True,
    ) -> tuple[Node, list[str]]: ...


class OnParseInput(Protocol):
    def __call__(self, *, event: Event) -> tuple[str, list[str], list[str]]: ...


class OnIntercept(Protocol):
    """Pipeline stage between node resolution and flow execution.

    Pass-through by default.  A Renderer (e.g. FormRenderer) can
    collect missing input before the command runs.
    """

    async def __call__(
        self,
        *,
        node: Node,
        tokens: list[str],
        session: Session,
        context: InputContext | None,
    ) -> tuple[Node, list[str]]: ...


class OnProjection(Protocol):
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
