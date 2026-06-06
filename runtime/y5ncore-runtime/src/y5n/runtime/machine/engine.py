from __future__ import annotations

import inspect
from collections.abc import Sequence
from typing import Protocol
from uuid import uuid4

from y5n.base.flow.primitives import (
    AwaitEvent,
    Background,
    Continue,
    Effect,
    EmitEvent,
    EmitView,
    Foreground,
    Outcome,
    StartTask,
    Stop,
)
from y5n.base.nodes import Node, NodePath, NodeSpace, Request
from y5n.base.projection import Projection
from y5n.base.runtime import Event
from y5n.base.runtime.input import InputContext
from y5n.runtime.flow import Flow, FlowCursor, FlowKind
from y5n.runtime.runtime import (
    Session,
)


class CommandEngine:

    DEFAULT_FLOW_KIND = FlowKind.USER

    def __init__(
        self,
        on_resolve_node: OnResolveNode,
        on_parse_input: OnParseInput,
        on_projection: OnProjection,
        on_start_task: OnTaskStart,
    ):
        self.on_resolve_command = on_resolve_node
        self.on_parse_input = on_parse_input
        self.on_projection = on_projection
        self.on_start_task = on_start_task

    # ----------------------------------------------------
    # PUBLIC API
    # ----------------------------------------------------

    async def setup(self, session: Session, node: Node) -> Flow | None:

        # TODO: Wie wollen wir darauf später reagieren?
        if not node.has_setup():
            return

        flow = Flow(
            id=uuid4().hex,
            node=node,
            event=Event(payload=node.key),
            cursor=FlowCursor("setup"),
            kind=self.DEFAULT_FLOW_KIND,
        )

        session.add_flow(flow)
        return flow

    async def dispatch(self, session: Session, event: Event) -> Flow | None:

        # session.execution.reset()
        # session.execution.step(ExecStep.EXECUTION_START)
        node: Node | None = None
        cmd, tokens, pipeline_commands = self.on_parse_input(event=event)
        if not cmd:
            return None

        # session.execution.step(
        #    ExecStep.COMMAND_RECEIVED,
        #    command=request.raw,
        # )

        # find node
        node, resolved_tokens = self.on_resolve_command(
            parent=session.get_current_node(),
            key=cmd,
            tokens=tokens,
            session=session,
        )

        tokens = resolved_tokens

        # TODO: Wie wollen wir darauf später reagieren?
        if not node.has_run():
            return None

        # session.execution.step(
        #    ExecStep.COMMAND_RESOLVED,
        #    command=command_type.key,
        #    controller=resolved_controller.id,
        # )

        # session.execution.step(
        #    ExecStep.COMMAND_PREPARED,
        #    command=command_type.key,
        #    controller=resolved_controller.id,
        # )

        flow = Flow(
            id=uuid4().hex,
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
            session._runtime_flow_id = flow.id  # type: ignore

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
            # 3.1 OUTCOME value
            # ----------------------------------
            if outcome.value is not None:
                if flow.pipeline:
                    outcome.control = Continue(outcome.value)
                else:
                    if not outcome.effects:
                        outcome.effects = [EmitView(outcome.value)]
                        pass

            # ----------------------------------
            # 4. EFFECTS
            # ----------------------------------
            if outcome.effects:
                await self._apply_effects(outcome.effects, session, flow)

            # ----------------------------------
            # 5. CONTROL (Scheduler übernimmt)
            # ----------------------------------
            if outcome.control is not None:
                return outcome

            # ----------------------------------
            # 6. Kein Ergebnis → nächster Step später
            # ----------------------------------
            return None

        except StopAsyncIteration:
            # aktueller Generator ist fertig
            cursor.pop()

            if not cursor.has_stack():
                return Outcome(control=Stop())

            return None

        finally:
            session._runtime_flow_id = None  # type: ignore

    # ----------------------------------------------------
    # INTERNAL
    # ----------------------------------------------------

    async def _apply_effects(
        self, effects: Sequence[Effect], session: Session, flow: Flow
    ):

        for effect in effects:

            if isinstance(effect, EmitView):
                if effect.persist:
                    flow.view = effect.view

                await self.on_projection(
                    session=session,
                    projection=effect.view,
                    ctx=flow.event.context,
                    job_id=flow.id,
                )

            elif isinstance(effect, Foreground):
                flow_id = effect.flow_id or flow.id
                session.set_foreground_flow(flow_id)

            elif isinstance(effect, Background):
                session.set_foreground_flow(None)

            elif isinstance(effect, EmitEvent):
                flow.inbox[effect.channel].append(effect.event)

            elif isinstance(effect, StartTask):
                self.on_start_task(
                    task=effect.handle,
                    flow=flow,
                    session=session,
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

            next_event = flow.pop_event(channel)
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
    def __call__(
        self,
        *,
        task,
        flow: Flow,
        session: Session,
    ) -> None: ...


class OnResolveNode(Protocol):
    def __call__(
        self,
        *,
        parent: NodePath,
        key: str,
        tokens: list[str] | None,
        session: Session,
    ) -> tuple[Node, list[str]]: ...


class OnParseInput(Protocol):
    def __call__(self, *, event: Event) -> tuple[str, list[str], list[str]]: ...


class OnProjection(Protocol):
    async def __call__(
        self,
        *,
        session: Session,
        projection: Projection,
        ctx: InputContext | None,
        job_id: str = "system",
    ) -> None: ...


class OnContinuePipeline(Protocol):
    async def __call__(self, session: Session, event: Event) -> None: ...
