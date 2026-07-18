from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

# Bedeutung für den Menschen
Role = Literal[
    "info",  # neutral
    "success",  # abgeschlossen
    "warning",  # Aufmerksamkeit
    "error",  # Problem
    "help",  # Erklärend
]

# Verhalten des Systems
# Was wird vom Nutzer / System erwartet? (interaktional)
Intent = Literal[
    "info",  # nur anzeigen
    "input",  # Eingabe erwartet
    "progress",  # Läuft weiter
    "transition",  # Zustand wechelt
]

ErrorKind = Literal[
    "validation",  # Field / Input
    "domain",  # Business / erwartbar
    "system",  # Infrastruktur
    "fatal",  # Crash / unrecoverable
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


class _DocumentHeader:

    # WHAT is this state?
    role: Role = "info"

    # HOW should the client interpret interaction?
    intent: Intent = "info"

    # Human communication
    title: str | None = None
    subtitle: str | None = None

    # Error semantics
    error_kind: ErrorKind | None = None
    error_code: str | None = None

    # Extension point (careful usage)
    meta: dict[str, Any] | None = None
