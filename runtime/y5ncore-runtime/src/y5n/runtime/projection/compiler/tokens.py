import re
from dataclasses import dataclass


@dataclass
class Token:
    type: str  # TEXT | OPEN | CLOSE | SELF
    tag: str | None = None
    attrs: dict[str, str] | None = None
    content: str | None = None


TAG_RE = re.compile(r"<(/?)(\w+)([^>]*)>")
ATTR_RE = re.compile(r'(\w+)="([^"]*)"')


def tokenize_text(text: str) -> list[Token]:
    text = _strip_remarks(text)
    return _tokenize(text)


# -------------
# HELPER
# -------------


def _strip_remarks(text: str) -> str:
    return re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)


def _tokenize(text: str) -> list[Token]:
    tokens: list[Token] = []
    pos = 0

    for match in TAG_RE.finditer(text):
        start, end = match.span()

        # Text davor
        if start > pos:
            tokens.append(Token(type="TEXT", content=text[pos:start]))

        is_close = match.group(1) == "/"
        tag = match.group(2)
        raw_attrs = match.group(3).strip()

        is_self = raw_attrs.endswith("/")
        if is_self:
            raw_attrs = raw_attrs[:-1].strip()

        attrs = dict(ATTR_RE.findall(raw_attrs)) if raw_attrs else {}

        if is_close:
            tokens.append(Token(type="CLOSE", tag=tag))
        elif is_self:
            tokens.append(Token(type="SELF", tag=tag, attrs=attrs))
        else:
            tokens.append(Token(type="OPEN", tag=tag, attrs=attrs))

        pos = end

    # Resttext
    if pos < len(text):
        tokens.append(Token(type="TEXT", content=text[pos:]))

    return tokens
