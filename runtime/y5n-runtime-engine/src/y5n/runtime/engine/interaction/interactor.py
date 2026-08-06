from __future__ import annotations

from y5n.runtime.api.flow.dsl import Pulse
from y5n.runtime.api.flow.patterns.public.form import Form
from y5n.runtime.api.flow.primitives import Continue
from y5n.runtime.api.runtime.context import current_context
from y5n.runtime.api.runtime.input import (
    InputContext,
    Interaction,
    Origin,
)
from y5n.runtime.api.runtime.invocation import CommandSignature
from y5n.runtime.engine.nodes import Node, UsageError
from y5n.runtime.engine.runtime import Session


class Interactor:
    """Decides between CLI and form mode for an invocation.

    In CLI mode (override, agent/scheduler caller, node.interaction=CLI)
    the request passes through unchanged. In form mode, _run_form creates
    a replacement node whose run handler drives a Form directly.
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
            sig = _matched_signature(node)
            if sig is not None:
                if not sig.has_required(tokens):
                    raise UsageError(usages=[sig.usage_data(node.key)])
                return await self._run_form(node, tokens, session)
            return node, tokens

        sig = _matched_signature(node)
        if sig is not None and sig.has_required(tokens):
            return node, tokens
        return await self._run_form(node, tokens, session)

    async def _run_form(
        self,
        node: Node,
        tokens: list[str],
        session: Session,
    ) -> tuple[Node, list[str]]:

        sig = _matched_signature(node)

        if sig is None:
            return node, tokens

        initial = None

        form_node = Node(
            key=node.key,
            run=self._make_form_handler(node, sig, initial),
            parent=node.parent,
        )
        return form_node, []

    def _make_form_handler(
        self,
        original_node: Node,
        sig: CommandSignature,
        initial: dict | None = None,
    ):

        async def handler(space):
            form = Form(
                fields=list(sig.params),
                title=sig.action or "",
                initial=dict(initial) if initial else None,
            )
            async for pulse in form.run():
                yield pulse

            ctx = current_context()
            lang = ctx.get("session", {}).get("lang", "en") if ctx else "en"
            invocation = sig.bind(
                form.values,
                path=str(original_node.path),
                lang=lang,
            )

            yield Pulse(control=Continue(), next_steps=[invocation])

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


def _matched_signature(node: Node) -> CommandSignature | None:
    sigs = node.signatures
    if not sigs:
        return None
    if len(sigs) == 1:
        return sigs[0]
    return sigs[0]
