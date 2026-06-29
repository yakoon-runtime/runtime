from __future__ import annotations

from y5n.api.dsl.patterns import Form
from y5n.base.nodes import Invocation, InvocationInput


class FormRenderer:
    """Collects parameter values for an Invocation via interactive Form prompts.

    Usage inside a flow handler::

        renderer = FormRenderer()
        async for outcome in renderer.render(invocation):
            yield outcome
        invocation_input = renderer.result
    """

    def __init__(self) -> None:
        self.result: InvocationInput | None = None

    async def render(self, invocation: Invocation):
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
