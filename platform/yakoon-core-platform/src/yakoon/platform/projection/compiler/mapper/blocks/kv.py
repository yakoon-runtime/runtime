from yakoon.base.projection.model import KvBlock, KvItemBlock

from ..core import is_element, is_whitespace


def map_kv(mapper, node):
    items: list[KvItemBlock] = []

    for child in node.children:
        if is_whitespace(child):
            continue

        if not is_element(child, "item"):
            raise ValueError("<kv> can only contain <item>")

        key = child.attrs.get("key")
        if not key:
            raise ValueError("<item> in <kv> requires 'key'")

        value = mapper._map_inline(child.children)

        items.append(
            KvItemBlock(
                id=None,
                key=key,
                value=value,
            )
        )

    return KvBlock(
        type="kv",
        id=None,
        items=items,
    )
