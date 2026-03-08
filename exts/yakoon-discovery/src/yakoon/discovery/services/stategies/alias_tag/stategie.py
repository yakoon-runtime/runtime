from __future__ import annotations

from yakoon.base.catalogs import CommandCatalogService, ControllerCatalogService
from yakoon.base.resources import ResourceLoader
from yakoon.base.runtime import Request, Session
from yakoon.base.runtime.controllers import resolve_resource
from yakoon.base.runtime.services import ServiceDirectory
from yakoon.discovery import ports as disc_ports
from yakoon.discovery.models.discovery import (
    Candidates,
    Capability,
    DiscoveryResult,
    NoMatch,
    Resolved,
)
from yakoon.discovery.models.parser import LookupIndex
from yakoon.discovery.ports import DiscoveryStrategy


def _split(line: str) -> tuple[str, str]:
    parts = line.strip().split(maxsplit=1)
    if not parts:
        return "", ""
    if len(parts) == 1:
        return parts[0].lower(), ""
    return parts[0].lower(), " " + parts[1]


class LookupAliasTagStrategy(DiscoveryStrategy):

    def __init__(
        self,
        services: ServiceDirectory,
        lookup_filename: str = "lookup",
    ) -> None:
        self._services = services
        self._lookup_filename = lookup_filename

    async def discover(self, session: Session, request: Request) -> DiscoveryResult:
        token, tail = self._parse_token(request)
        if not token:
            return NoMatch()

        owner_ids = self._resolve_owner_ids(session)
        if not owner_ids:
            return NoMatch()

        all_alias: list[Capability] = []
        all_tags: list[Capability] = []

        for owner_id in owner_ids:
            text = self._load_lookup_text(session, owner_id)
            if not text:
                continue

            idx = self._parse_index(text)
            if not idx:
                continue

            visible = self._visible_keys(session, owner_id)
            alias_caps, tag_caps = self._match_owner(
                owner_id=owner_id,
                token=token,
                tail=tail,
                idx=idx,
                visible=visible,
            )
            all_alias.extend(alias_caps)
            all_tags.extend(tag_caps)

        if len(all_alias) == 1:
            return Resolved(capability=all_alias[0])
        if len(all_alias) > 1:
            return Candidates(items=all_alias)
        if all_tags:
            return Candidates(items=all_tags)
        return NoMatch()

    def _parse_token(self, request: Request) -> tuple[str, str]:
        head, tail = _split(request.raw)
        return head, tail

    def _resolve_owner_ids(self, session: Session) -> list[str]:
        active_id = session.get_active_controller()
        if not active_id:
            return []

        commands = self._services.get(CommandCatalogService)
        resolve_space = commands.for_resolve_context(active_id)

        owner_ids: list[str] = []
        seen: set[str] = set()
        for ci in resolve_space:
            if ci.controller_id in seen:
                continue
            seen.add(ci.controller_id)
            owner_ids.append(ci.controller_id)
        return owner_ids

    def _load_lookup_text(self, session: Session, owner_id: str) -> str | None:
        controllers = self._services.get(ControllerCatalogService)
        loader = self._services.get(ResourceLoader)

        ctrl = controllers.get(owner_id)
        if not ctrl or not ctrl.resources or not ctrl.resources.lookup:
            return None

        ref = resolve_resource(
            ctrl.resources,
            i18n_root=ctrl.resources.lookup,
            lang=session.lang,
            key=self._lookup_filename,
        )

        try:
            return loader.load_text(ref)
        except LookupError:
            return None

    def _parse_index(self, text: str):
        parser = self._services.get(disc_ports.LookupParser)
        idx = parser.parse(text)
        if not idx or not getattr(idx, "commands", None):
            return None
        return idx

    def _visible_keys(self, session: Session, owner_id: str) -> set[str]:
        commands = self._services.get(CommandCatalogService)
        return {c.key for c in commands.for_controller_visible(owner_id, session)}

    def _match_owner(
        self,
        *,
        owner_id: str,
        token: str,
        tail: str,
        idx: LookupIndex,
        visible: set[str],
    ) -> tuple[list[Capability], list[Capability]]:

        alias_caps: list[Capability] = []
        tag_caps: list[Capability] = []

        for key in idx.alias_index.get(token, []):
            if key in visible:
                alias_caps.append(
                    Capability(
                        command_key=key + tail,
                        controller_id=owner_id,
                        score=1.0,
                        reason="alias",
                    )
                )

        for key in idx.tag_index.get(token, []):
            if key in visible:
                tag_caps.append(
                    Capability(
                        command_key=key + tail,
                        controller_id=owner_id,
                        score=0.7,
                        reason="tag",
                    )
                )

        return alias_caps, tag_caps
