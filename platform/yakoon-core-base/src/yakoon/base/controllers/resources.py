from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath

from yakoon.base.resources.resource import ResourceRef, _clean_rel


def resolve_resource(
    refs: ResourceReferences,
    *,
    i18n_root: str | None,
    lang: str | None = None,
    key: str | None = None,
) -> ResourceRef:
    """
    Resolve a resource location inside a package.

    - refs.package: module/package root
    - root: e.g. refs.contracts / refs.man / refs.workflows / refs.lookup
    - key: an optional relative key below the root (e.g. "system/help" or "crm/customer/create")

    Returns a ResourceRef(package=..., path="...") with a normalized relative path.

    Raises ValueError if root is None.
    """
    if not i18n_root:
        raise ValueError("Resource root is not configured for this controller.")

    root = i18n_root.format(lang=lang)
    root_rel = _clean_rel(root)
    if not key:
        return ResourceRef(package=refs.package, path=root_rel)

    key_rel = _clean_rel(key)
    full = str(PurePosixPath(root_rel) / key_rel)
    return ResourceRef(package=refs.package, path=full)


@dataclass(frozen=True, slots=True)
class ResourceReferences:
    """
    Pure metadata: explicit roots relative to the module/package root.

    No concatenation rules, no defaults, no magic.
    Each root is either:
      - None (resource type not provided by this controller)
      - a relative path like "contracts/core" or "man" etc.
    """

    package: str

    # Contracts / ViewSpecs (formerly templates)
    contracts: str | None = "resources/{lang}/contracts/"

    assets: str | None = "resources/{lang}/assets/"

    # Man pages (can be inside contracts or separate; controller decides)
    man: str | None = "resources/{lang}/manuals/"

    # Workflows (yaml)man
    workflows: str | None = "resources/workflows/"

    # Lookup / discovery docs (yaml)
    lookup: str | None = "resources/{lang}/discovery/"

    def clone(self) -> ResourceReferences:
        """Return a copy of this ResourceReferences."""
        return ResourceReferences(
            self.package,
            self.contracts,
            self.assets,
            self.man,
            self.workflows,
            self.lookup,
        )
