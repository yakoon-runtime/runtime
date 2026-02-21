from yakoon.platform.settings import settings


async def ask_AI(prompt: str, context: dict) -> str:

    backend = settings.ai.backend
    if backend == "openai":
        from yakoon.platform.plugins.ai.agent_openai import ask_openai

        return await ask_openai(prompt, context)
    elif backend == "ollama":
        from yakoon.platform.plugins.ai.agent_ollama import ask_ollama

        return await ask_ollama(prompt, context)
    else:
        raise RuntimeError(f"Unbekannter AI-Backend: {backend}")
