from .nodes import ElementNode, TextNode
from .tokens import Token


def build_ast(tokens: list[Token]) -> ElementNode:

    root = ElementNode(tag="root")
    stack = [root]

    for t in tokens:
        if t.type == "TEXT":
            if t.content:
                stack[-1].children.append(TextNode(text=t.content))

        elif t.type == "OPEN":
            node = ElementNode(tag=t.tag, attrs=t.attrs or {})
            stack[-1].children.append(node)
            stack.append(node)

        elif t.type == "SELF":
            node = ElementNode(tag=t.tag, attrs=t.attrs or {})
            stack[-1].children.append(node)

        elif t.type == "CLOSE":
            if len(stack) == 1:
                raise ValueError(f"Unexpected closing tag </{t.tag}>")

            if stack[-1].tag != t.tag:
                raise ValueError(
                    f"Mismatched closing tag </{t.tag}>, expected </{stack[-1].tag}>"
                )

            stack.pop()

    if len(stack) != 1:
        raise ValueError(f"Unclosed tag <{stack[-1].tag}>")

    return root
