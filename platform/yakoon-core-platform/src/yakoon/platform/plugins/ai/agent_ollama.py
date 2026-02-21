import httpx

from yakoon.platform.settings import settings


async def ask_ollama(prompt: str, context: dict) -> str:
    payload = {
        "model": context.get("model", "mistral"),
        "prompt": prompt,
        "stream": False,
    }
    async with httpx.AsyncClient(timeout=settings.ai.ollama.timeout) as client:
        response = await client.post(settings.ai.ollama.url, json=payload)
        response.raise_for_status()
        return response.json()["response"]
