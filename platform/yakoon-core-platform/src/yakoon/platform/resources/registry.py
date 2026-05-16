from __future__ import annotations

from dataclasses import dataclass

from yakoon.base.resources import ResourceRef


class ProjectionRegistry:

    def __init__(self):
        self._localized: dict[tuple[str, str, str], _ProjectionResource] = {}

    # ----------------------------------
    # REGISTER
    # ----------------------------------

    def register(
        self,
        scope: str,
        key: str,
        resource: ResourceRef,
        lang: str,
        renderer: str | None = None,
        theme: str | None = None,
        priority: int = 0,
    ) -> None:

        if (scope, key, lang) in self._localized:
            raise ValueError(f"Resource already registered: {key}")

        self._localized[(scope, key, lang)] = _ProjectionResource(
            key=key,
            resource=resource,
            lang=lang,
            renderer=renderer,
            theme=theme,
            priority=priority,
        )

    # ----------------------------------
    # RESOLVE
    # ----------------------------------

    def resolve(
        self,
        scope: str,
        key: str,
        lang: str,
    ) -> ResourceRef | None:

        entry = self._localized.get((scope, key, lang))
        if not entry:
            return None

        return entry.resource


# ----------------------------------------
# INTERNAL RESOURCE
# ----------------------------------------


@dataclass(slots=True)
class _ProjectionResource:

    key: str
    resource: ResourceRef
    lang: str | None = None
    renderer: str | None = None
    theme: str | None = None
    priority: int = 0
