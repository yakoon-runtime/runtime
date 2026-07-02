from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Any

from y5n.base.flow.dsl import Outcome
from y5n.base.flow.patterns.public.form import Form
from y5n.base.nodes import BoundInvocation, Invocation, InvocationInput


class FormRenderer:
    """Renders an Invocation as an interactive form.

    Converts the parameter definitions (args + options) of an Invocation
    into a Form object and collects field input sequentially (render).
    After successful collection, bound() produces a BoundInvocation.

    initial may carry pre-filled values (e.g. from OnPrepareInput).
    The FormRenderer itself has no knowledge of add, edit, duplicate —
    it only receives values.
    """

    def __init__(self) -> None:
        self.result: InvocationInput | None = None

    async def render(
        self,
        invocation: Invocation,
        initial: InvocationInput | None = None,
    ) -> AsyncGenerator[AsyncGenerator[Outcome, Any], None]:
        all_fields = list(invocation.params)

        titles: dict[str, str] = {}
        for param in invocation.params:
            titles[param.key] = param.title or param.key.title()

        form = Form(
            fields=all_fields,
            title=invocation.action or "",
            initial=dict(initial.values) if initial else None,
            titles=titles,
        )

        for param in invocation.params:
            yield form.ask(
                key=param.key,
                title=param.title or param.key.title(),
                policy=param.policy,
            )

        self.result = InvocationInput(values=dict(form.data))

    def bound(self, invocation: Invocation) -> BoundInvocation:
        assert self.result is not None
        return invocation.bind(self.result)
