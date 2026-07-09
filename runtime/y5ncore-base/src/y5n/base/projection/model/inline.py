from dataclasses import dataclass
from typing import Any, Literal


@dataclass(frozen=True, slots=True)
class InlineText:
    type: Literal["text"] = "text"
    text: str = ""


@dataclass(frozen=True, slots=True)
class InlineCode:
    type: Literal["code"] = "code"
    children: list["Inline"] | None = None


@dataclass(frozen=True, slots=True)
class InlineArg:
    type: Literal["arg"] = "arg"
    children: list["Inline"] | None = None


@dataclass(frozen=True, slots=True)
class InlineLink:
    type: Literal["link"] = "link"
    href: str = ""
    children: list["Inline"] | None = None


@dataclass(frozen=True, slots=True)
class InlineSelect:
    type: Literal["select"] = "select"
    value: Any = None
    children: list["Inline"] | None = None


@dataclass(frozen=True, slots=True)
class InlineCmd:
    type: Literal["cmd"] = "cmd"
    command: str = ""
    variant: str | None = None
    navigable: bool | None = None
    resolvable: bool | None = None
    contextual: bool | None = None
    children: list["Inline"] | None = None


@dataclass(frozen=True, slots=True)
class InlineStrong:
    type: Literal["strong"] = "strong"
    children: list["Inline"] | None = None


@dataclass(frozen=True, slots=True)
class InlineEm:
    type: Literal["em"] = "em"
    children: list["Inline"] | None = None


@dataclass(frozen=True, slots=True)
class InlineUnderline:
    type: Literal["underline"] = "underline"
    children: list["Inline"] | None = None


@dataclass(frozen=True, slots=True)
class InlineMark:
    type: Literal["mark"] = "mark"
    variant: str | None = None
    children: list["Inline"] | None = None


@dataclass(frozen=True, slots=True)
class InlineSpace:
    type: Literal["space"] = "space"
    count: int | None = None


@dataclass(frozen=True, slots=True)
class InlineBreak:
    type: Literal["break"] = "break"
    count: int | None = None


Inline = (
    InlineText
    | InlineCode
    | InlineArg
    | InlineLink
    | InlineSelect
    | InlineCmd
    | InlineStrong
    | InlineSpace
    | InlineEm
    | InlineUnderline
    | InlineMark
    | InlineBreak
)
