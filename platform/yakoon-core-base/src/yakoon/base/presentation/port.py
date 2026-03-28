from typing import Protocol

from .view import View


class ViewSpecParser(Protocol):

    def parse_spec(
        self,
        yaml_text: str,
        *,
        section_key: str | None = None,
        base_id: str | None = None,
    ) -> View: ...
