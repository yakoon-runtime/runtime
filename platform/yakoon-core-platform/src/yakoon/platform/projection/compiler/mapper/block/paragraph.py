from yakoon.base.projection.model import ParagraphBlock


def map_paragraph(mapper, node):
    inline = mapper._map_inline(node.children)

    return ParagraphBlock(
        id=None,
        text=inline,
    )
