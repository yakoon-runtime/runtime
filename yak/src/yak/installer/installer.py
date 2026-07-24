from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from yak.distribution.models import PackName
from yak.installation.models import Installation
from yak.repository.artifact import ArtifactStore


class Installer:
    def __init__(self, artifact_store: ArtifactStore) -> None:
        self._artifacts = artifact_store

    def install(self, installation: Installation) -> None:
        venv_dir = installation.root / ".venv"
        python = self._ensure_venv(venv_dir)

        for pack in installation.packs:
            artifact = self._artifacts.get_artifact(pack)
            if artifact is None:
                continue
            self._install_pack(python, artifact)

    def _ensure_venv(self, path: Path) -> Path:
        if not (path / "bin" / "python").exists():
            subprocess.run(
                [sys.executable, "-m", "venv", str(path)],
                check=True, capture_output=True,
            )
        python = path / "bin" / "python"
        subprocess.run(
            [str(python), "-m", "pip", "install", "--upgrade", "pip"],
            check=True, capture_output=True,
        )
        return python

    def _install_pack(self, python: Path, pack_dir: Path) -> None:
        has_project_file = (
            (pack_dir / "pyproject.toml").exists()
            or (pack_dir / "setup.py").exists()
            or (pack_dir / "setup.cfg").exists()
        )
        if not has_project_file:
            return

        result = subprocess.run(
            [str(python), "-m", "pip", "install", "-e", str(pack_dir)],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            import warnings

            warnings.warn(
                f"pip install failed for {pack_dir.name}: "
                f"{result.stderr.strip()}"
            )
