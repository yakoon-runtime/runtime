from typing import Protocol


class OnProject(Protocol):
    async def __call__(self, *, name: str, lang: str, state: dict | None = None) -> object: ...
