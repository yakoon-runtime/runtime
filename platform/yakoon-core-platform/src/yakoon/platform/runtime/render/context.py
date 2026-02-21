from __future__ import annotations

from dataclasses import dataclass

from yakoon.base.models.resource import ResourceRef


@dataclass(frozen=True, slots=True)
class RenderContext:
    resource: ResourceRef
    lang: str
