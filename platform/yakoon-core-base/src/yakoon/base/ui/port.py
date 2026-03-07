from typing import Protocol

from yakoon.base.ui.view_spec import ViewSpec


class ViewSpecParser(Protocol):

    def parse_spec(
        self,
        yaml_text: str,
        *,
        section_key: str | None = None,
        base_id: str | None = None,
    ) -> ViewSpec: ...
