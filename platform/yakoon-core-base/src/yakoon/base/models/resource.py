from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath


@dataclass(frozen=True, slots=True)
class ResourceRef:
    package: str
    path: str  # relative inside package, posix style


def _clean_rel(p: str) -> str:
    pp = PurePosixPath(p)
    if pp.is_absolute():
        pp = PurePosixPath(*pp.parts[1:])
    return str(pp)
