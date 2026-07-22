from __future__ import annotations

from typing import cast

from y5n.runtime.api.flow.dsl import Outcome
from y5n.runtime.api.flow.patterns.public.form import Form
from y5n.runtime.api.flow.primitives import Continue
from y5n.runtime.api.nodes import (
    Invocation,
    InvocationInput,
    Node,
    UsageError,
)
from y5n.runtime.api.nodes.request.builder import RequestBuilder
from y5n.runtime.api.runtime.input import (
    InputContext,
    Interaction,
    OnPrepareInput,
    Origin,
)
from y5n.runtime.api.runtime.sessions import Session as BaseSession
from y5n.runtime.runtime import Session


class Interactor:
    """Decides between CLI and form mode for an invocation.

    In CLI mode (override, agent/scheduler caller, node.interaction=CLI)
    the request passes through unchanged. In form mode, _run_form creates
    a replacement node whose run handler drives a Form directly.

    If a node provides OnPrepareInput via its port hierarchy, initial
    values are loaded before rendering (e.g. entity data on edit).
    The Interactor itself has no knowledge about the origin of these
    values.
    """

    async def intercept(
        self,
        node: Node,
        tokens: list[str],
        session: Session,
        context: InputContext | None,
    ) -> tuple[Node, list[str]]:

        override = _pop_override(tokens)

        caller = context.origin if context else None
        policy = resolve_interaction(
            caller, override, node.interaction, session.interaction
        )

        if policy is Interaction.CLI:
            return node, tokens

        if policy is Interaction.FORM:
            inv = _matched_invocation(node)
            if inv is not None:
                if not inv.has_required(tokens):
                    raise UsageError(usages=[inv.usage_data(node.key)])
                return await self._run_form(node, tokens, session)
            return node, tokens

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
                    node=node,
                    invocation=inv,
                    tokens=tokens,
                    session=cast(BaseSession, session),
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
            form = Form(
                fields=list(inv.params),
                title=inv.action or "",
                initial=dict(initial.values) if initial else None,
            )
            async for outcome in form.run():
                yield outcome

            bound = inv.bind(InvocationInput(values=form.values))
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
