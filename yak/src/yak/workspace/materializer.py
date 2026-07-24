from __future__ import annotations

from pathlib import Path

from yak.distribution.models import PackName


class Materializer:
    def __init__(self, packs_root: Path, workspace_root: Path) -> None:
        self._packs_root = packs_root
        self._workspace_root = workspace_root

    def materialize(self, packs: list[PackName]) -> Path:
        workspace = self._workspace_root
        workspace.mkdir(parents=True, exist_ok=True)

        packs_dir = workspace / "packs"
        packs_dir.mkdir(exist_ok=True)

        for pack in packs:
            src = self._packs_root / pack
            dst = packs_dir / pack
            if src.is_dir() and not dst.exists():
                dst.symlink_to(src, target_is_directory=True)

        return workspace
