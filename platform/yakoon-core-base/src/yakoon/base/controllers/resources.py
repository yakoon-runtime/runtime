from __future__ import annotations

from dataclasses import dataclass


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

    # Contracts / Projections (formerly templates)
    contracts: str = "resources/{lang}/contracts/{cmd_key}"

    # Man pages (can be inside contracts or separate; controller decides)
    man: str = "resources/{lang}/manuals/{cmd_key}"

    # Resources like files or images
    assets: str = "resources/{lang}/assets/"

    # Lookup / discovery docs (yaml)
    lookup: str = "resources/{lang}/discovery/"

    def to_dict(self) -> dict:
        return {
            "package": self.package,
            "contracts": self.contracts,
            "assets": self.assets,
            "man": self.man,
        }
