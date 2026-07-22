from y5n.runtime.api.dsl import foreground, out_text, receive
from y5n.runtime.api.llm import LLMMessage, LLMRequest
from y5n.runtime.api.nodes import NodeSpace
from y5n.runtime.api.ports import OnCallLLM


async def run(space: NodeSpace):
    llm = space.ports.get(OnCallLLM)
    messages: list[LLMMessage] = []

    yield out_text("Chat start — /end beendet die Unterhaltung.", mode="append")

    while True:
        yield foreground()
        yield out_text("> ", mode="append")
        event = yield receive()
        text = event.payload.strip()

        if text == "/end":
            yield out_text("Chat beendet.", mode="append")
            return

        if not text:
            continue

        messages.append(LLMMessage(role="user", content=text))
        result = await llm.complete(LLMRequest(messages=messages))
        messages.append(LLMMessage(role="assistant", content=result.text))

        yield out_text(f"You: {text}", mode="append")
        yield out_text(f"Assistant: {result.text}", mode="append")
