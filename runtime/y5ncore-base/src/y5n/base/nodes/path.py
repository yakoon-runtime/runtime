from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NodePath:

    parts: tuple[str, ...]

    # ----------------------------------
    # STRING
    # ----------------------------------

    @classmethod
    def from_string(cls, value: str | None) -> NodePath:

        if value is None:
            return cls(())

        value = value.strip("/")
        if not value:
            return cls(())

        return cls(tuple(p for p in value.split("/") if p))

    def __str__(self) -> str:

        return "/" + "/".join(p for p in self.parts if p.strip("/"))

    # ----------------------------------
    # EXTENSIONS
    # ----------------------------------

    def child(self, key: str) -> NodePath:

        return NodePath((*self.parts, key))

    def join(self, path: NodePath) -> NodePath:
        return NodePath(self.parts + path.parts)

    # ----------------------------------
    # HIERARCHY
    # ----------------------------------

    @classmethod
    def root(cls) -> NodePath:
        return cls(())

    @property
    def parent(self) -> NodePath:

        if not self.parts:
            return self

        return NodePath(self.parts[:-1])

    # ----------------------------------
    # SECTIONS
    # ----------------------------------

    @property
    def first(self) -> str | None:

        if not self.parts:
            return None

        return self.parts[0]

    @property
    def last(self) -> str | None:

        if not self.parts:
            return None

        return self.parts[-1]
