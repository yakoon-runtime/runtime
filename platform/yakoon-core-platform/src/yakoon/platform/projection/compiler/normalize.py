import re

from .nodes import ElementNode, TextNode

PRESERVE_TAGS = {
    "code",
    "pre",
}


def normalize_ast(root: ElementNode) -> None:
    _normalize_node(root, preserve=False)


# -----------------------
# INTERNAL METHODS
# -----------------------


def _normalize_node(
    node: ElementNode,
    preserve: bool,
) -> None:

    preserve = preserve or node.tag in PRESERVE_TAGS

    for child in node.children:

        if isinstance(child, TextNode):
            if preserve:
                continue

            child.text = _collapse_whitespace(child.text)

        elif isinstance(child, ElementNode):

            _normalize_node(child, preserve)


def _collapse_whitespace(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    return text.strip()
