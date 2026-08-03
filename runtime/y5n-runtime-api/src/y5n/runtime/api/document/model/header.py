from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

# Meaning for the human
Role = Literal[
    "info",  # neutral
    "success",  # completed
    "warning",  # attention
    "error",  # problem
    "help",  # explanatory
]

ErrorKind = Literal[
    "validation",  # field / input
    "domain",  # business / expected
    "system",  # infrastructure
    "fatal",  # crash / unrecoverable
]


@dataclass(frozen=True, slots=True)
class ViewUI:
    secret: bool = False


@dataclass(frozen=True, slots=True)
class DocumentMeta:
    ui: ViewUI | None = None


@dataclass(frozen=True, slots=True)
class DocumentHeader:
    """
    Document-level presentation metadata.

    This is the stable header that hosts may render as:
      - title / subtitle
      - role-based framing / icon / color
      - future document-level presentation hints
    """

    role: Role | None = "info"
    title: str | None = None
    subtitle: str | None = None
    error_kind: ErrorKind | None = None
    error_code: str | None = None
    meta: dict[str, Any] | DocumentMeta | None = None
