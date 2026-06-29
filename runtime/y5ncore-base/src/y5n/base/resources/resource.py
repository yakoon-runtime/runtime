from __future__ import annotations

import posixpath
from dataclasses import dataclass, replace
from pathlib import PurePosixPath


@dataclass(frozen=True, slots=True)
class ResourceRef:

    package: str
    path: str  # relative inside package, posix style
    encoding: str = "utf-8"
    exts: tuple[str, ...] = (".yak",)

    def clone(self, **kwargs) -> ResourceRef:
        return replace(self, **kwargs)

    def child(self, rel: str) -> ResourceRef:
        # security + normalization: no absolute, no traversal
        if rel.startswith("/"):
            raise ValueError("ResourceRef.child() expects a relative path")
        if ".." in rel.split("/"):
            raise ValueError("ResourceRef.child() does not allow '..' traversal")

        new_path = posixpath.normpath(posixpath.join(self.path, rel))
        if new_path.startswith("../") or new_path == "..":
            raise ValueError("ResourceRef.child() resulted in path traversal")
        return self.clone(path=new_path)


def _clean_rel(p: str) -> str:
    pp = PurePosixPath(p)
    if pp.is_absolute():
        pp = PurePosixPath(*pp.parts[1:])
    return str(pp)
