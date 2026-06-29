from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Any

from y5n.base.flow.dsl import Outcome
from y5n.base.flow.patterns.public.form import Form
from y5n.base.nodes import BoundInvocation, Invocation, InvocationInput


class FormRenderer:

    def __init__(self) -> None:
        self.result: InvocationInput | None = None

    async def render(
        self, invocation: Invocation
    ) -> AsyncGenerator[AsyncGenerator[Outcome, Any], None]:
        form = Form()

        for param in invocation.args:
            yield form.ask(
                key=param.key,
                title=param.title or param.key.title(),
                policy=param.policy,
            )

        for param in invocation.options:
            yield form.ask(
                key=param.key,
                title=f"{param.title or param.key.title()} (optional)",
                policy=param.policy,
            )

        self.result = InvocationInput(values=dict(form.data))

    def bound(self, invocation: Invocation) -> BoundInvocation:
        assert self.result is not None
        return invocation.bind(self.result)
