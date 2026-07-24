from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from yak.distribution.models import Mount, PackName
from yak.repository.artifact import ArtifactStore
from yak.workspace.models import Workspace


def _target_for(mounts: list[Mount], pack: PackName) -> str | None:
    for m in mounts:
        if m.pack == pack:
            return m.target
    return None


class Materializer:
    def __init__(self, artifact_store: ArtifactStore) -> None:
        self._artifacts = artifact_store

    def materialize(
        self,
        workspace_root: Path,
        distribution: str,
        packs: list[PackName],
        mounts: list[Mount] | None = None,
    ) -> Workspace:
        workspace_root.mkdir(parents=True, exist_ok=True)

        structure = workspace_root / "structure"
        structure.mkdir(exist_ok=True)

        mounts = mounts or []
        for pack in packs:
            artifact = self._artifacts.get_artifact(pack)
            if artifact is None:
                continue
            pack_struct = artifact / "structure"
            if not pack_struct.is_dir():
                continue

            # Find explicit mount target for this pack, otherwise mount at pack name
            target_rel = _target_for(mounts, pack) or pack
            target = structure / target_rel.strip("/")
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.exists():
                target.symlink_to(pack_struct, target_is_directory=True)

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
