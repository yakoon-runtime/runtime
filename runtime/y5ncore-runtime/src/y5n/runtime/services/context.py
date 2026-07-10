from __future__ import annotations

from pathlib import Path


class ContextService:

    def __init__(self, root_path: str | None = None):
        self._root = Path(root_path).resolve() if root_path else None

    def path(self, subdir: str | None = None) -> list[str]:
        if not self._root:
            return []

        dirs: list[str] = []
        current = (self._root / subdir).resolve() if subdir else self._root

        while current.is_relative_to(self._root):
            path_file = current / ".yakoon" / "path"
            if path_file.is_file():
                lines = path_file.read_text().splitlines()
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        dirs.append(str((current / line).resolve()))
            if current == self._root:
                break
            current = current.parent

        return dirs
