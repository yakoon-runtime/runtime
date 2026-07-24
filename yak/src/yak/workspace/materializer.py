from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from yak.distribution.models import PackName
from yak.workspace.models import Workspace


class Materializer:
    def __init__(self, packs_root: Path) -> None:
        self._packs_root = packs_root

    def materialize(
        self,
        workspace_root: Path,
        distribution: str,
        packs: list[PackName],
    ) -> Workspace:
        workspace_root.mkdir(parents=True, exist_ok=True)

        # structure/ — symlinks into pack structure/ dirs
        structure = workspace_root / "structure"
        structure.mkdir(exist_ok=True)

        for pack in packs:
            pack_struct = self._packs_root / pack / "structure"
            link = structure / pack
            if pack_struct.is_dir() and not link.exists():
                link.symlink_to(pack_struct, target_is_directory=True)

        # workspace.toml — identity
        now = datetime.now(timezone.utc)
        self._write_manifest(workspace_root, distribution, packs, now)

        return Workspace(
            path=workspace_root,
            distribution=distribution,
            packs=packs,
            created=now,
            updated=now,
        )

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
