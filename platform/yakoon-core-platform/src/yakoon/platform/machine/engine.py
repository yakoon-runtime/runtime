from __future__ import annotations

import inspect
from collections.abc import Sequence
from typing import Protocol
from uuid import uuid4

from yakoon.base.flow.primitives import (
    AutoFocus,
    AwaitEvent,
    ClearFocus,
    Continue,
    Effect,
    EmitEvent,
    EmitView,
    Outcome,
    SetFocus,
    Stop,
)
from yakoon.base.nodes import Node, NodePath, Request, RuntimeContext
from yakoon.base.projection import Projection
from yakoon.base.runtime import InputEvent
from yakoon.base.runtime.input import InputContext
from yakoon.platform.flow import Flow, FlowCursor, FlowKind
from yakoon.platform.runtime import (
    Session,
)


class CommandEngine:

    DEFAULT_FLOW_KIND = FlowKind.USER

    def __init__(
        self,
        on_resolve_node: OnResolveNode,
        on_parse_input: OnParseInput,
        on_projection: OnProjection,
    ):
        self.on_resolve_command = on_resolve_node
        self.on_parse_input = on_parse_input
        self.on_projection = on_projection

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
            event=InputEvent(node.key, tokens=[]),
            cursor=FlowCursor("on_setup"),
            kind=self.DEFAULT_FLOW_KIND,
        )

        session.add_flow(flow)
        return flow

    async def dispatch(self, session: Session, event: InputEvent) -> Flow | None:

        # session.execution.reset()
        # session.execution.step(ExecStep.EXECUTION_START)
        node: Node | None = None
        event, pipeline_commands = self.on_parse_input(event=event)
        if not event or not event.command:
            return None

        # session.execution.step(
        #    ExecStep.COMMAND_RECEIVED,
        #    command=request.raw,
        # )

        # find node
        node, tokens = self.on_resolve_command(
            parent=session.get_current_node(),
            key=event.command,
            tokens=event.tokens,
            session=session,
        )

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
            event=event.update(command=node.key, tokens=tokens),
            cursor=FlowCursor("on_run"),
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

            if isinstance(item, InputEvent):
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
                await self.on_projection(
                    session=session,
                    projection=effect.view,
                    ctx=flow.event.context,
                    job_id=flow.id,
                )

            elif isinstance(effect, AutoFocus):
                session.set_interaction(flow.id)

            elif isinstance(effect, EmitEvent):
                flow.inbox[effect.channel].append(effect.event)

            elif isinstance(effect, SetFocus):
                session.set_interaction(effect.flow_id)

            elif isinstance(effect, ClearFocus):
                session.set_interaction(None)

    async def _next_step(
        self,
        flow: Flow,
        node: Node,
        event: InputEvent,
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
            event.command,
            event.tokens,
            event.payload,
            session.lang,
        )

        return await flow.cursor.next(
            node,
            RuntimeContext(
                request=request,
                session=session,
                ports=node.ports,
                ports_from=node.ports_from,
                node=node.describe,
                metadata=dict(node.metadata),
            ),
        )


# ----------------------------------
# PORTS
# ----------------------------------


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
    def __call__(self, *, event: InputEvent) -> tuple[InputEvent, list[str]]: ...


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
    async def __call__(self, session: Session, event: InputEvent) -> None: ...
