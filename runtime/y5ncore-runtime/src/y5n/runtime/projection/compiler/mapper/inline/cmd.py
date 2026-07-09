from y5n.base.projection.model import InlineCmd


def _bool(value: str | None) -> bool | None:
    if value is None:
        return None
    return value.lower() in ("true", "1", "yes")


def map_cmd(mapper, node):
    command = node.attrs.get("command")
    if not command:
        raise ValueError("<cmd> requires 'command'")

    children = mapper._map_inline(node.children)

    if not children:
        raise ValueError("<cmd> requires label")

    return InlineCmd(
        command=command,
        variant=node.attrs.get("variant"),
        navigable=_bool(node.attrs.get("navigable")),
        resolvable=_bool(node.attrs.get("resolvable")),
        contextual=_bool(node.attrs.get("contextual")),
        children=children,
    )
