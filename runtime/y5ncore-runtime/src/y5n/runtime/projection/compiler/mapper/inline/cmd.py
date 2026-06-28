from y5n.base.projection.model import InlineCmd


def map_cmd(mapper, node):
    command = node.attrs.get("command")
    if not command:
        raise ValueError("<cmd> requires 'command'")

    children = mapper._map_inline(node.children)

    if not children:
        raise ValueError("<cmd> requires label")

    variant = node.attrs.get("variant")

    return InlineCmd(
        command=command,
        variant=variant,
        children=children,
    )
