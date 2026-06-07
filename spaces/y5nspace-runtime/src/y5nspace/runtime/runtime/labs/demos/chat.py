from __future__ import annotations

from y5n.api.dsl import out_text
from y5n.api.nodes import NodeSpace
from y5n.api.ports import OnCallLLM
from y5n.base.llm import LLMMessage, LLMRequest


async def run(space: NodeSpace):
    prompt = " ".join(space.request.args())
    if not prompt:
        yield out_text("Usage: chat <message>")
        return

    llm = space.ports.get(OnCallLLM)
    result = await llm.complete(
        LLMRequest(
            messages=[
                LLMMessage(
                    role="system",
                    content="Du bist ein hilfreicher Assistent.",
                ),
                LLMMessage(role="user", content=prompt),
            ]
        )
    )
    yield out_text(result.text)
