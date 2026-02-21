from yakoon.platform.settings import settings


async def ask_openai(prompt: str, context: dict) -> str:

    try:
        import openai  # type: ignore

        raise NotImplementedError()
        openai.api_key = settings.ai.openai.api_key
    except Exception as exc:
        raise RuntimeError("Open AI not installed.") from exc

    model = context.get("model", "gpt-4")
    response = await openai.ChatCompletion.acreate(
        model=model, messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()
