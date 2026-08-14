from __future__ import annotations

import inspect
from collections.abc import Sequence
from typing import Protocol

from y5n.runtime.api.flow.dsl import out_text
from y5n.runtime.api.flow.primitives import AwaitEvent, Effect, Pulse, Stop
from y5n.runtime.api.runtime import Event, InputContext, Interaction
from y5n.runtime.engine.flow import Flow, FlowCursor, FlowKind
from y5n.runtime.engine.interaction import resolve_interaction
from y5n.runtime.engine.nodes import Node
from y5n.runtime.engine.runtime import Session
from y5n.runtime.engine.runtime.invocation import (
    derive_invocation_context,
    error_payload,
    establish_invocation_context,
)

ERROR_NODE = "/usr/bin/err"


class CommandEngine:
    """Core flow execution engine.

    Steps a flow's async generator, applies effects (emit, start, dispatch),
    and returns the pulse control to the scheduler.
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
        try:
            node, resolved_tokens = self.on_resolve_command(
                key=cmd,
                tokens=tokens,
                session=session,
                strict=strict,
            )
        except Exception as error:
            # The invocation could not be resolved (NodeNotFound,
            # PermissionDenied, UsageError). The error creates a new
            # invocation: dispatch the error node like any other command.
            # Guard the recursion baseline — if the error node itself
            # cannot be resolved, there is no further invocation to make.
            if event.error is not None:
                return None
            return await self.dispatch(session, error_event(error, event))

        tokens = resolved_tokens

        try:
            node, tokens = await self._on_intercept(
                node=node,
                tokens=tokens,
                session=session,
                context=event.context,
            )
        except Exception as error:
            if event.error is not None:
                return None
            return await self.dispatch(session, error_event(error, event))

        if not node.has_run():
            return None

        flow_id = session.next_flow_id()

        invocation = derive_invocation_context(
            node=node,
            session=session,
            flow_id=flow_id,
            tokens=tokens,
            error=event.error,
        )

        flow = Flow(
            id=flow_id,
            node=node,
            tokens=tokens,
            pipeline=pipeline,
            event=event.update(payload=node.key),
            cursor=FlowCursor("run"),
            kind=self.DEFAULT_FLOW_KIND,
            invocation=invocation,
        )

        session.add_flow(flow)
        return flow

    async def step_flow(self, flow: Flow, session: Session) -> Pulse | None:

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
                        return Pulse(control=Stop())
                    return None

            # ----------------------------------
            # 2. SUBGENERATOR (SUBFLOW / CALL)
            # ----------------------------------
            if inspect.isasyncgen(item):
                cursor.push(item)
                return None

            # ----------------------------------
            # 3. OUTCOME directly
            # ----------------------------------
            assert isinstance(item, Pulse)
            pulse = item

            # ----------------------------------
            # 4. PIPELINE
            # ----------------------------------
            if pulse.next_steps:
                flow.pipeline = list(pulse.next_steps) + list(flow.pipeline or [])

            # ----------------------------------
            # 5. EFFECTS
            # ----------------------------------
            if pulse.effects:
                await self._on_apply_effects(pulse.effects, session, flow)

            # ----------------------------------
            # 6. CONTROL (scheduler takes over)
            # ----------------------------------
            if pulse.control is not None:
                return pulse

            # ----------------------------------
            # 7. No pulse → next step later
            # ----------------------------------
            return None

        except StopAsyncIteration:
            # current generator is done
            cursor.pop()

            if not cursor.has_stack():
                return Pulse(control=Stop())

            return None

        except Exception as error:
            # The flow's generator failed. This is a boundary, not a
            # failure of the scheduler: the exception is translated into
            # a new invocation on the error node and the SAME flow is
            # pointed at it. The flow's id, channel and session stay —
            # only the next step changes (ADR: an error creates a new
            # invocation).
            return await self._route_error(flow, session, error)

    async def _route_error(
        self,
        flow: Flow,
        session: Session,
        error: Exception,
    ) -> Pulse | None:
        """Translate an exception into an error invocation on this flow.

        The first failure routes the flow to the error node; the error
        node's own failure terminates at the boot fallback (``error_depth``
        guards the recursion baseline). The engine only knows the ABI
        convention ``/usr/bin/err`` — never error handling.
        """
        if flow.error_depth >= 1:
            flow.error_depth += 1
            return out_text("Internal Error")

        flow.error_depth += 1

        try:
            error_node, _ = self.on_resolve_command(
                key=ERROR_NODE,
                tokens=[],
                session=session,
                strict=True,
            )
        except Exception:
            # The error node itself cannot be resolved (not found, denied).
            # Terminate at the boot fallback.
            return out_text("Internal Error")

        if not error_node.has_run():
            return out_text("Internal Error")

        flow.node = error_node
        flow.invocation = derive_invocation_context(
            node=error_node,
            session=session,
            flow_id=flow.id,
            tokens=[],
            error=error_payload(error),
        )
        flow.cursor = FlowCursor("run")
        flow.tokens = []
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

        if flow.invocation is not None:
            establish_invocation_context(flow.invocation)

        return await flow.cursor.next(node)


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


def error_event(error: Exception, source: Event | None = None) -> Event:
    """Translate an exception into an error invocation event.

    A boundary (shell, bus, exception, …) produces an event; the error
    node is a normal command the dispatcher resolves like any other.
    """
    return Event(
        payload=ERROR_NODE,
        error=error_payload(error),
        context=source.context if source else None,
    )
