# yakoon/platform/runtime/message/spec.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True, slots=True)
class InlineText:
    """
    Plain inline text.

    Usage (YAML):
        - { type: "text", text: "Hello world" }
    """

    type: Literal["text"]
    text: str


@dataclass(frozen=True, slots=True)
class InlineCode:
    """
    Inline code fragment (semantic, not Markdown).

    Usage (YAML):
        - { type: "code", code: "man" }

    Console example:
        `man`
    """

    type: Literal["code"]
    code: str


@dataclass(frozen=True, slots=True)
class InlineLink:
    """
    Inline link (label + href).

    Usage (YAML):
        - { type: "link", text: "Docs", href: "https://example.com" }

    Console example:
        Docs (https://example.com)
    """

    type: Literal["link"]
    text: str
    href: str


Inline = InlineText | InlineCode | InlineLink
