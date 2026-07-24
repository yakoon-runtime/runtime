from __future__ import annotations

from pathlib import Path

from yak.distribution.models import Distribution, PackName


class TargetResolver:
    def __init__(
        self,
        local_repos: Path,
        builtin_distributions: Path,
    ) -> None:
        self._local_repos = local_repos
        self._builtin = builtin_distributions

    def resolve(self, target: str) -> Distribution | None:
        # 1. Exact path to a .toml file
        path = Path(target)
        if path.suffix == ".toml" and path.exists():
            return self._load(path)

        # 2. Builtin distribution (e.g. "desktop", "crm")
        builtin = self._builtin / f"{target}.toml"
        if builtin.exists():
            return self._load(builtin)

        # 3. Pack manifest (e.g. "crm" → repos/y5napp-crm/pack.toml)
        pack = self._local_repos / f"y5napp-{target}" / "pack.toml"
        if pack.exists():
            return self._load(pack)

        return None

    @staticmethod
    def _load(path: Path) -> Distribution:
        import tomllib

        with open(path, "rb") as f:
            data = tomllib.load(f)
        return Distribution(
            name=data["name"],
            version=data.get("version", "0.1"),
            packs=[
                TargetResolver._pack_ref(p)
                for p in data.get("packs", data.get("pack", []))
            ],
            distributions=[
                TargetResolver._pack_ref(p)
                for p in data.get("distributions", data.get("distribution", []))
            ],
        )

    @staticmethod
    def _pack_ref(raw: str | dict) -> "PackReference":
        from yak.distribution.models import PackReference, VersionConstraint

        if isinstance(raw, str):
            return PackReference(name=PackName(raw))
        name = raw.get("name", "")
        version = raw.get("version")
        return PackReference(
            name=PackName(name),
            version=VersionConstraint(version) if version else None,
        )
