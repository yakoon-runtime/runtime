from __future__ import annotations

from pathlib import Path

from yak.distribution.models import Distribution, PackName, PackReference, VersionConstraint


class LocalRepository:
    def __init__(self, packs_root: Path) -> None:
        self._root = packs_root

    def resolve_distribution(self, name: str) -> Distribution | None:
        dist_path = self._root / f"y5napp-{name}" / "pack.toml"
        if not dist_path.exists():
            return None
        return self._parse(dist_path)

    def resolve_pack(self, name: PackName) -> bool:
        return (self._root / name).is_dir()

    def _parse(self, path: Path) -> Distribution:
        import tomllib

        with open(path, "rb") as f:
            data = tomllib.load(f)
        return Distribution(
            name=data["name"],
            version=data.get("version", "0.1"),
            packs=[self._pack_ref(p) for p in data.get("packs", data.get("pack", []))],
            distributions=[self._pack_ref(p) for p in data.get("distributions", data.get("distribution", []))],
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
