from __future__ import annotations

from y5n.base.document.model import TableBlock, TableColumn
from y5n.runtime.document.compiler.nodes import ElementNode, TextNode


def map_table(mapper, node):
    columns: list[TableColumn] = []
    rows: list[list[str]] = []

    for child in node.children:
        if isinstance(child, TextNode):
            if child.text.strip():
                raise ValueError(
                    f"<table> does not support text content: {child.text!r}"
                )
            continue

        assert isinstance(child, ElementNode)

        if child.tag == "column":
            key = child.attrs.get("key", "")
            if not key:
                raise ValueError("<column> requires key attribute")
            title = child.attrs.get("title", key)
            columns.append(TableColumn(key=key, title=title))

        elif child.tag == "row":
            row: list[str] = []
            for cell in child.children:
                if isinstance(cell, TextNode):
                    text = cell.text.strip()
                    if text:
                        row.append(text)
                elif isinstance(cell, ElementNode) and cell.tag == "cell":
                    row.append(_extract_text(cell))
                else:
                    raise ValueError(
                        f"<row> only supports text and <cell>, got <{cell.tag}>"
                    )
            rows.append(row)

        else:
            raise ValueError(
                f"<table> only supports <column> and <row>, got <{child.tag}>"
            )

    variant = node.attrs.get("variant")
    raw_selectable = node.attrs.get("selectable", "true")
    selectable = raw_selectable.lower() in ("true", "1", "")

    return TableBlock(
        columns=columns,
        rows=rows,
        variant=variant,
        selectable=selectable,
    )


def _extract_text(node: ElementNode) -> str:
    parts: list[str] = []
    for child in node.children:
        if isinstance(child, TextNode):
            parts.append(child.text)
        elif isinstance(child, ElementNode):
            parts.append(_extract_text(child))
    return "".join(parts).strip()
