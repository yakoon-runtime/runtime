from typing import Protocol

from .resource import ResourceRef


class ResourceLoader(Protocol):

    def load_text(
        self,
        ref: ResourceRef,
        *,
        exts: tuple[str, ...] = (".yaml", ".yml", ".json"),
        encoding: str = "utf-8",
    ) -> str: ...
