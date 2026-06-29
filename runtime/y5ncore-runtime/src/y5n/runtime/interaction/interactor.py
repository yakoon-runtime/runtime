from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Any, Protocol

from y5n.base.flow.dsl import Outcome
from y5n.base.flow.primitives import Continue
from y5n.base.nodes import BoundInvocation, Invocation, Node
from y5n.base.nodes.request.builder import RequestBuilder
from y5n.base.runtime.input import InputContext, Interaction, Origin
from y5n.runtime.runtime import Session


class Interactor:

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
        policy = resolve_interaction(caller, override, session.interaction)

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
            return self._run_form(node, tokens)

        inv = _matched_invocation(node)
        if inv is not None and inv.has_required(tokens):
            return node, tokens
        return self._run_form(node, tokens)

    def _run_form(
        self,
        node: Node,
        tokens: list[str],
    ) -> tuple[Node, list[str]]:

        inv = _matched_invocation(node)

        if inv is None:
            return node, tokens

        form_node = Node(
            key=node.key,
            run=self._make_form_handler(node, inv),
            ports=node.ports,
            parent=node.parent,
        )
        return form_node, []

    def _make_form_handler(
        self,
        original_node: Node,
        inv: Invocation,
    ):

        async def handler(space):
            async for outcome in self._on_form_render(inv):
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
    preference: Interaction,
) -> Interaction:
    if override is not None:
        return Interaction(override)
    if caller in (Origin.AGENT, Origin.SCHEDULER):
        return Interaction.CLI
    return preference


# ----------------------------------
# INTERNALS
# ----------------------------------


def _pop_override(tokens: list[str]) -> str | None:
    for prefix in ("--cli", "--form", "--auto"):
        if prefix in tokens:
            tokens.remove(prefix)
            return prefix.lstrip("--")
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
        self, invocation: Invocation
    ) -> AsyncGenerator[AsyncGenerator[Outcome, Any], None]: ...


class OnFormBind(Protocol):
    def __call__(self, invocation: Invocation) -> BoundInvocation: ...
