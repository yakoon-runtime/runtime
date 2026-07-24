from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from yak.distribution.models import PackName, ToolReference
from yak.installation.models import Installation
from yak.repository.artifact import ArtifactStore


class Installer:
    def __init__(self, artifact_store: ArtifactStore) -> None:
        self._artifacts = artifact_store

    def install(
        self,
        installation: Installation,
        tools: list[ToolReference] | None = None,
        sdk_path: Path | None = None,
    ) -> None:
        venv_dir = installation.root / ".venv"
        python = self._ensure_venv(venv_dir)

        projects: list[Path] = []
        if sdk_path is not None and self._has_project_file(sdk_path):
            projects.append(sdk_path)

        for pack in installation.packs:
            artifact = self._artifacts.get_artifact(pack)
            if artifact is None:
                continue
            projects.extend(self._find_projects(artifact))

        if tools:
            for tool in tools:
                artifact = self._artifacts.get_artifact(PackName(tool.name))
                if artifact is None:
                    continue
                projects.extend(self._find_projects(artifact))

        if projects:
            self._pip_install_all(python, projects)

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

    def _find_projects(self, pack_dir: Path) -> list[Path]:
        if self._has_project_file(pack_dir):
            return [pack_dir]
        projects: list[Path] = []
        for child in sorted(pack_dir.iterdir()):
            if child.is_dir() and self._has_project_file(child):
                projects.append(child)
        return projects

    @staticmethod
    def _has_project_file(directory: Path) -> bool:
        return (
            (directory / "pyproject.toml").exists()
            or (directory / "setup.py").exists()
            or (directory / "setup.cfg").exists()
        )

    def _pip_install_all(self, python: Path, projects: list[Path]) -> None:
        cmd = [str(python), "-m", "pip", "install"]
        for proj in projects:
            cmd.extend(["-e", str(proj)])
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            import warnings

            warnings.warn(
                f"pip install failed:\n{result.stderr.strip()}"
            )
