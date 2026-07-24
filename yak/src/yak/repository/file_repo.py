from __future__ import annotations

from pathlib import Path

from yak.distribution.models import (
    Distribution,
    PackName,
    PackReference,
    VersionConstraint,
)


class FileRepository:
    def __init__(self, *roots: Path, builtin_dists: Path | None = None) -> None:
        self._roots = list(roots)
        self._builtin = builtin_dists

    def resolve_distribution(self, name: str) -> Distribution | None:
        # 1. Builtin distributions (e.g. "desktop" → yak/distributions/desktop.toml)
        if self._builtin is not None:
            builtin = self._builtin / f"{name}.toml"
            if builtin.exists():
                return self._parse(builtin)

        # 2. Pack manifests across all roots
        for root in self._roots:
            dist_path = root / f"y5napp-{name}" / "pack.toml"
            if dist_path.exists():
                return self._parse(dist_path)
        return None

    def resolve_pack(self, name: PackName) -> bool:
        for root in self._roots:
            if self._find_manifest(root, name):
                return True
        return False

    def _find_manifest(self, root: Path, name: PackName) -> Path | None:
        for candidate in (root / name, root / f"y5napp-{name}"):
            manifest = candidate / "pack.toml"
            if manifest.exists():
                return manifest
        return None

    def _parse(self, path: Path) -> Distribution:
        import tomllib

        with open(path, "rb") as f:
            data = tomllib.load(f)
        return Distribution(
            name=data["name"],
            version=data.get("version", "0.1"),
            packs=[self._pack_ref(p) for p in data.get("packs", data.get("pack", []))],
            distributions=[
                self._pack_ref(p)
                for p in data.get("distributions", data.get("distribution", []))
            ],
        )

    @staticmethod
    def _pack_ref(raw: str | dict) -> PackReference:
        if isinstance(raw, str):
            return PackReference(name=PackName(raw))
        name = raw.get("name", "")
        version = raw.get("version")
        return PackReference(
            name=PackName(name),
            version=VersionConstraint(version) if version else None,
        )
