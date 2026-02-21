from __future__ import annotations

from yakoon.base import ports
from yakoon.base.commands.request import Request
from yakoon.base.directories.service import ServiceDirectory
from yakoon.base.resources.reference import resolve_resource
from yakoon.base.runtime.session import Session
from yakoon.discovery.models.discovery import (
    Candidates,
    Capability,
    DiscoveryResult,
    NoMatch,
    Resolved,
)
from yakoon.discovery.ports import DiscoveryStrategy


def _query_line(request: Request) -> str:
    fn = getattr(request, "free_text", None)
    if callable(fn):
        v = fn()
        if isinstance(v, str) and v.strip():
            return v.strip()
    v = getattr(request, "raw", None)
    if isinstance(v, str) and v.strip():
        return v.strip()
    fn = getattr(request, "arg", None)
    if callable(fn):
        v = fn(0)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return ""


def _first_token(line: str) -> str:
    return line.split(maxsplit=1)[0].strip().lower() if line else ""


class LookupAliasTagStrategy(DiscoveryStrategy):

    def __init__(
        self,
        services: ServiceDirectory,
        # loader: FileLoader,
        # parser,
        lookup_filename: str = "lookup",
    ) -> None:
        self._services = services
        # self._loader = loader
        # self._parser = parser
        self._lookup_filename = lookup_filename

    async def discover(self, session: Session, request: Request) -> DiscoveryResult:
        token = _first_token(_query_line(request))
        if not token:
            return NoMatch()

        controller_id = session.get_active_controller()
        if not controller_id:
            return NoMatch()

        controllers = self._services.get(ports.ControllerCatalogService)
        ctrl = controllers.get(controller_id)
        if not ctrl or not ctrl.resources or not ctrl.resources.lookup:
            return NoMatch()

        resources = ctrl.resources
        if not resources:
            raise RuntimeError("ControllerInfo has no Resources.")

        # Build resource reference
        ref = resolve_resource(
            resources,
            i18n_root=resources.lookup,
            lang=session.lang,
            key=self._lookup_filename,
        )

        try:
            text = self._loader.load_text(ref)
        except LookupError:
            return NoMatch()

        index = self._parser.parse(text)
        if not index.commands:
            return NoMatch()

        command_service = self._services.get(ports.CommandCatalogService)

        visible = {
            c.key
            for c in command_service.for_controller_visible(controller_id, session)
        }

        alias_hits: list[str] = []
        tag_hits: list[str] = []

        for command_key, entry in index.commands.items():
            if command_key not in visible:
                continue
            if token in entry.aliases:
                alias_hits.append(command_key)
            if token in entry.tags:
                tag_hits.append(command_key)

        if len(alias_hits) == 1:
            return Resolved(
                capability=Capability(
                    command_key=alias_hits[0],
                    controller_id=controller_id,
                    score=1.0,
                    reason="alias",
                )
            )

        if len(alias_hits) > 1:
            return Candidates(
                items=[
                    Capability(
                        command_key=k,
                        controller_id=controller_id,
                        score=1.0,
                        reason="alias",
                    )
                    for k in alias_hits
                ]
            )

        if tag_hits:
            return Candidates(
                items=[
                    Capability(
                        command_key=k,
                        controller_id=controller_id,
                        score=0.7,
                        reason="tag",
                    )
                    for k in tag_hits
                ]
            )

        return NoMatch()
