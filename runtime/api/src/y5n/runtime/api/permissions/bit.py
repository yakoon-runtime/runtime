from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class PermBit(StrEnum):
    READ = "r"
    WRITE = "w"
    EXECUTE = "x"


@dataclass(frozen=True)
class PermBits:
    r: bool = False
    w: bool = False
    x: bool = False

    @classmethod
    def from_str(cls, s: str) -> PermBits:
        s = s or ""
        return cls(r="r" in s, w="w" in s, x="x" in s)

    def __bool__(self) -> bool:
        return self.r or self.w or self.x

    def union(self, other: PermBits) -> PermBits:
        return PermBits(r=self.r or other.r, w=self.w or other.w, x=self.x or other.x)

    def subtract(self, other: PermBits) -> PermBits:
        # remove bits present in other
        return PermBits(
            r=self.r and not other.r, w=self.w and not other.w, x=self.x and not other.x
        )
