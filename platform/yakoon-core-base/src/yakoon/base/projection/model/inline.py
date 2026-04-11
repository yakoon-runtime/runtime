from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal


@dataclass(frozen=True, slots=True)
class InlineText:
    type: Literal["text"] = "text"
    text: str = ""


@dataclass(frozen=True, slots=True)
class InlineCode:
    type: Literal["code"] = "code"
    text: str = ""


@dataclass(frozen=True, slots=True)
class InlineLink:
    type: Literal["link"] = "link"
    text: str = ""
    href: str = ""


@dataclass(frozen=True, slots=True)
class InlineSelect:
    type: Literal["select"] = "select"
    text: str = ""
    value: Any = None


@dataclass(frozen=True, slots=True)
class InlineCmd:
    type: Literal["cmd"] = "cmd"
    command: str = ""
    text: str = ""


Inline = InlineText | InlineCode | InlineLink | InlineSelect | InlineCmd
