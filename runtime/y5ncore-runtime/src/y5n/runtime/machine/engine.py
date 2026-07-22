from __future__ import annotations

import inspect
from collections.abc import Sequence
from typing import Protocol, cast

from y5n.runtime.engine.flow.primitives import AwaitEvent, Effect, Outcome, Stop
from y5n.runtime.engine.nodes import Node, NodeSpace, Request
from y5n.runtime.engine.runtime import Event, InputContext, Interaction
from y5n.runtime.engine.runtime.sessions import Session as BaseSession
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
        on_intercept: OnIntercept,
        on_apply_effects: OnApplyEffects,
    ):
        self.on_resolve_command = on_resolve_node
        self.on_parse_input = on_parse_input
        self._on_intercept = on_intercept
        self._on_apply_effects = on_apply_effects

    # ----------------------------------------------------
    # PUBLIC API
    # ----------------------------------------------------

    async def setup(self, session: Session, node: Node) -> Flow | None:

        if not node.has_setup():
            return None

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
        cmd, tokens, pipeline = self.on_parse_input(event=event)
        if not cmd:
            return None

        # Determine strictness before resolve — lenient allows
        # the Interceptor to collect missing params via form.
        caller = event.context.origin if event.context else None
        policy = resolve_interaction(
            caller, None, Interaction.INHERIT, session.interaction
        )
        strict = policy is Interaction.CLI

        # find node
        node, resolved_tokens = self.on_resolve_command(
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
            tokens=tokens,
            pipeline=pipeline,
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
            assert isinstance(item, Outcome)
            outcome = item

            # ----------------------------------
            # 4. PIPELINE
            # ----------------------------------
            if outcome.next_steps:
                flow.pipeline = list(outcome.next_steps) + list(flow.pipeline or [])

            # ----------------------------------
            # 5. EFFECTS
            # ----------------------------------
            if outcome.effects:
                await self._on_apply_effects(outcome.effects, session, flow)

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
                session=cast(BaseSession, session),
                ports=node.ports,
                ports_from=node.ports_from,
                resources=node.resources,
                flow_id=flow.id,
            ),
        )


# ----------------------------------
# PORTS
# ----------------------------------


class OnApplyEffects(Protocol):
    async def __call__(
        self,
        effects: Sequence[Effect],
        session: Session,
        flow: Flow,
    ) -> None: ...


class OnResolveNode(Protocol):
    def __call__(
        self,
        *,
        key: str,
        tokens: list[str] | None,
        session: Session,
        strict: bool = True,
    ) -> tuple[Node, list[str]]: ...


class OnParseInput(Protocol):
    def __call__(self, *, event: Event) -> tuple[str, list[str], list[str]]: ...


class OnIntercept(Protocol):
    """Pipeline stage between node resolution and flow execution.

    Collects missing input (e.g. via a Form) before the command runs.
    """

    async def __call__(
        self,
        *,
        node: Node,
        tokens: list[str],
        session: Session,
        context: InputContext | None,
    ) -> tuple[Node, list[str]]: ...
