from __future__ import annotations

import os
import platform

from y5n.api.nodes import NodeSpace
from y5n.api.ports import OnCallLLM
from y5n.llm.providers.openai_compat import OpenAICompatibleProvider


async def setup(space: NodeSpace):

    system = platform.system()
    release = platform.release()
    print(f"[os] system context: {system} {release}")

    space.ports.provide(
        OnCallLLM,
        OpenAICompatibleProvider(
            base_url="https://api.mistral.ai/v1",
            model="mistral-large-latest",
            api_key=os.environ.get("MISTRAL_API_KEY")
            or "a1aToqqdXvEkxLlcUYwWZmkyXqBGD5Lz",
        ),
    )
