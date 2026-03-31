from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol

from .model import Projection

if TYPE_CHECKING:
    from yakoon.base.resources.resource import ResourceRef


class Projector(Protocol):
    """
    Unified presentation API.

    A projector renders one state, streams it to the host, may pause on
    interactive blocks, and optionally returns collected values.
    """

    async def project(
        self,
        name: str,
        **data: Any,
    ) -> Projection: ...


class ProjectorFactory(Protocol):
    async def create(self, resource: ResourceRef, session) -> Projector: ...


class ProjectionParser(Protocol):

    def parse_spec(
        self,
        yaml_text: str,
        *,
        section_key: str | None = None,
        base_id: str | None = None,
    ) -> Projection: ...
