from __future__ import annotations

from y5n.api.dsl import out_text
from y5n.api.nodes import NodeSpace
from y5n.api.ports import OnCallLLM
from y5n.base.llm import LLMRequest


async def run(space: NodeSpace):
    prompt = " ".join(space.request.args())
    if not prompt:
        yield out_text("Usage: llm <prompt>")
        return

    llm = space.ports.get(OnCallLLM)
    result = await llm.complete(LLMRequest(prompt=prompt))
    yield out_text(result.text)
