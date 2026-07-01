from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Any, Protocol, cast

from y5n.base.flow.dsl import Outcome
from y5n.base.flow.primitives import Continue
from y5n.base.nodes import BoundInvocation, Invocation, InvocationInput, Node
from y5n.base.nodes.request.builder import RequestBuilder
from y5n.base.runtime.input import InputContext, Interaction, OnPrepareInput, Origin
from y5n.base.runtime.sessions import Session as BaseSession
from y5n.runtime.runtime import Session


class Interactor:
    """Decides between CLI and form mode for an invocation.

    In CLI mode (override, agent/scheduler caller, node.interaction=CLI)
    the request passes through unchanged. In form mode, _run_form creates
    a replacement node whose run handler collects fields via FormRenderer.

    If a node provides OnPrepareInput via its port hierarchy, initial
    values are loaded before rendering (e.g. entity data on edit).
    The Interactor itself has no knowledge about the origin of these
    values.
    """

    def __init__(self, on_form_render: OnFormRender, on_form_bind: OnFormBind):
        self._on_form_render = on_form_render
        self._on_form_bind = on_form_bind

    async def intercept(
        self,
        node: Node,
        tokens: list[str],
        session: Session,
        context: InputContext | None,
    ) -> tuple[Node, list[str]]:

        override = _pop_override(tokens)

        caller = context.origin if context else None
        policy = resolve_interaction(caller, override, node.interaction, session.interaction)

        if policy is Interaction.CLI:
            return node, tokens

        if policy is Interaction.FORM:
            inv = _matched_invocation(node)
            if (
                inv is not None
                and inv.has_required(tokens)
                and any(t.startswith("--") for t in tokens)
            ):
                return node, tokens
            return await self._run_form(node, tokens, session)

        inv = _matched_invocation(node)
        if inv is not None and inv.has_required(tokens):
            return node, tokens
        return await self._run_form(node, tokens, session)

    async def _run_form(
        self,
        node: Node,
        tokens: list[str],
        session: Session,
    ) -> tuple[Node, list[str]]:

        inv = _matched_invocation(node)

        if inv is None:
            return node, tokens

        initial = None
        if node.ports is not None:
            try:
                on_prepare = node.ports.get(OnPrepareInput)
                initial = await on_prepare(
                    node=node, invocation=inv, tokens=tokens, session=cast(BaseSession, session),
                )
            except KeyError:
                pass

        form_node = Node(
            key=node.key,
            run=self._make_form_handler(node, inv, initial),
            ports=node.ports,
            parent=node.parent,
        )
        return form_node, []

    def _make_form_handler(
        self,
        original_node: Node,
        inv: Invocation,
        initial: InvocationInput | None = None,
    ):

        async def handler(space):
            async for outcome in self._on_form_render(inv, initial=initial):
                yield outcome

            bound = self._on_form_bind(inv)
            req = RequestBuilder().build(
                bound, command=original_node.key, lang=space.session.lang
            )

            yield Outcome(control=Continue(), next_steps=[req])

        return handler


# ----------------------------------
# PUBLICS
# ----------------------------------


def resolve_interaction(
    caller: str | None,
    override: str | None,
    node_interaction: Interaction,
    session_interaction: Interaction,
) -> Interaction:
    if override is not None:
        return Interaction(override)
    if caller in (Origin.AGENT, Origin.SCHEDULER):
        return Interaction.CLI
    if node_interaction is not Interaction.INHERIT:
        return node_interaction
    return session_interaction


# ----------------------------------
# INTERNALS
# ----------------------------------


def _pop_override(tokens: list[str]) -> str | None:
    for prefix in ("--cli", "--form", "--inherit"):
        if prefix in tokens:
            tokens.remove(prefix)
            return prefix.removeprefix("--")
    return None


def _matched_invocation(node: Node) -> Invocation | None:
    invs = node.invocations
    if not invs:
        return None
    if len(invs) == 1:
        return invs[0]
    return invs[0]


# ----------------------------------
# PORTS
# ----------------------------------


class OnFormRender(Protocol):
    def __call__(
        self,
        invocation: Invocation,
        initial: InvocationInput | None = None,
    ) -> AsyncGenerator[AsyncGenerator[Outcome, Any], None]: ...


class OnFormBind(Protocol):
    def __call__(self, invocation: Invocation) -> BoundInvocation: ...
