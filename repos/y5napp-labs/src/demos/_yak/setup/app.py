import os

from y5n.runtime.api.nodes import NodeSpace
from y5n.runtime.api.ports import OnCallLLM
from y5n.runtime.llm.providers.openai_compat import OpenAICompatibleProvider


async def run(space: NodeSpace):
    space.ports.provide(
        OnCallLLM,
        OpenAICompatibleProvider(
            base_url="https://api.mistral.ai/v1",
            model="mistral-large-latest",
            api_key=os.environ.get("MISTRAL_API_KEY")
            or "a1aToqqdXvEkxLlcUYwWZmkyXqBGD5Lz",
        ),
    )
