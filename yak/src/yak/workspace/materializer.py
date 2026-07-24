from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from yak.distribution.models import PackName
from yak.workspace.models import Workspace


class Materializer:
    def __init__(self, *pack_roots: Path) -> None:
        self._pack_roots = list(pack_roots)

    @property
    def pack_roots(self) -> list[Path]:
        return list(self._pack_roots)

    def materialize(
        self,
        workspace_root: Path,
        distribution: str,
        packs: list[PackName],
    ) -> Workspace:
        workspace_root.mkdir(parents=True, exist_ok=True)

        structure = workspace_root / "structure"
        structure.mkdir(exist_ok=True)

        for pack in packs:
            src = self._find_pack_dir(pack)
            if src is None:
                continue
            pack_struct = src / "structure"
            link = structure / pack
            if pack_struct.is_dir() and not link.exists():
                link.symlink_to(pack_struct, target_is_directory=True)

        now = datetime.now(UTC)
        self._write_manifest(workspace_root, distribution, packs, now)

        return Workspace(
            path=workspace_root,
            distribution=distribution,
            packs=packs,
            created=now,
            updated=now,
        )

    def _find_pack_dir(self, name: PackName) -> Path | None:
        for root in self._pack_roots:
            if root.name == name and root.is_dir():
                return root
            if (root / name).is_dir():
                return root / name
            if (root / f"y5napp-{name}").is_dir():
                return root / f"y5napp-{name}"
        return None

    def _write_manifest(
        self,
        root: Path,
        distribution: str,
        packs: list[PackName],
        now: datetime,
    ) -> None:
        packs_str = "\n".join(f'  "{p}",' for p in packs)
        manifest = f"""\
[workspace]
distribution = "{distribution}"
version = "1"
created = "{now.isoformat()}"
updated = "{now.isoformat()}"
packs = [
{packs_str}
]
"""
        with open(root / "workspace.toml", "w") as f:
            f.write(manifest)
