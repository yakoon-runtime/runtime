from __future__ import annotations

from yakoon.base import ports
from yakoon.base.commands.request import Request
from yakoon.base.directories.service import ServiceDirectory
from yakoon.base.resources.reference import resolve_resource
from yakoon.base.runtime.session import Session
from yakoon.discovery import ports as disc_ports
from yakoon.discovery.models.discovery import (
    Candidates,
    Capability,
    DiscoveryResult,
    NoMatch,
    Resolved,
)
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
    line = request.raw
    head, tail = _split(line)

    token = head
    if not token:
        return NoMatch()

    active_id = session.get_active_controller()
    if not active_id:
        return NoMatch()

    controllers = self._services.get(ports.ControllerCatalogService)
    commands = self._services.get(ports.CommandCatalogService)
    loader = self._services.get(ports.FileLoader)
    parser = self._services.get(disc_ports.LookupParser)

    is_shell_active = controllers.is_shell(active_id)

    # Resolve-space via CommandInfo (plugin-safe)
    resolve_space = commands.iter_resolve_space(
        active_id,
        is_shell_active=is_shell_active,
    )

    # Deterministic owner order as they appear in resolve-space
    owner_ids: list[str] = []
    seen_owner: set[str] = set()
    for ci in resolve_space:
        if ci.controller_id in seen_owner:
            continue
        seen_owner.add(ci.controller_id)
        owner_ids.append(ci.controller_id)

    # Per-call caches
    index_cache: dict[str, object | None] = {}  # owner_id -> LookupIndex | None
    visible_cache: dict[str, set[str]] = {}  # owner_id -> set(command_key)

    def _visible_keys(owner_id: str) -> set[str]:
        v = visible_cache.get(owner_id)
        if v is not None:
            return v
        v = {c.key for c in commands.for_controller_visible(owner_id, session)}
        visible_cache[owner_id] = v
        return v

    def _load_index(owner_id: str):
        if owner_id in index_cache:
            return index_cache[owner_id]

        ctrl = controllers.get(owner_id)
        if not ctrl or not ctrl.resources or not ctrl.resources.lookup:
            index_cache[owner_id] = None
            return None

        resources = ctrl.resources
        ref = resolve_resource(
            resources,
            i18n_root=resources.lookup,
            lang=session.lang,
            key=self._lookup_filename,
        )

        try:
            text = loader.load_text(ref)
        except LookupError:
            index_cache[owner_id] = None
            return None

        idx = parser.parse(text)
        index_cache[owner_id] = idx
        return idx

    alias_caps: list[Capability] = []
    tag_caps: list[Capability] = []

    for owner_id in owner_ids:
        idx = _load_index(owner_id)
        if not idx or not getattr(idx, "commands", None):
            continue

        visible = _visible_keys(owner_id)

        for command_key, entry in idx.commands.items():
            if command_key not in visible:
                continue

            if token in entry.aliases:
                alias_caps.append(
                    Capability(
                        command_key=command_key + tail,
                        controller_id=owner_id,
                        score=1.0,
                        reason="alias",
                    )
                )

            if token in entry.tags:
                tag_caps.append(
                    Capability(
                        command_key=command_key + tail,
                        controller_id=owner_id,
                        score=0.7,
                        reason="tag",
                    )
                )

    if len(alias_caps) == 1:
        return Resolved(capability=alias_caps[0])

    if len(alias_caps) > 1:
        return Candidates(items=alias_caps)

    if tag_caps:
        return Candidates(items=tag_caps)

    return NoMatch()
