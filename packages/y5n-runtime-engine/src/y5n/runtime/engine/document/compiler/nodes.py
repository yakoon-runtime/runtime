from dataclasses import dataclass, field


@dataclass
class Node:
    pass


@dataclass
class TextNode(Node):
    text: str


@dataclass
class ElementNode(Node):
    tag: str
    attrs: dict[str, str] = field(default_factory=dict)
    children: list[Node] = field(default_factory=list)
