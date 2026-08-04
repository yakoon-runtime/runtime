"""SDK generated models — from_dict/to_dict round trips.

Guards the generated YDS model against regressions in the union
deserializers and the symmetric dict conversion.
"""

from __future__ import annotations

import pytest
from y5n.sdk.models import (
    Action,
    Actions,
    Collapsible,
    Document,
    Field,
    Fields,
    Flow,
    Header,
    Heading,
    Image,
    InlineArg,
    InlineBreak,
    InlineCmd,
    InlineCode,
    InlineEm,
    InlineLink,
    InlineMark,
    InlineSelect,
    InlineSpace,
    InlineStrong,
    InlineText,
    InlineUnderline,
    Kv,
    KvItem,
    List,
    ListItem,
    Paragraph,
    Pre,
    Rule,
    Section,
    Spacer,
    Stack,
    Table,
    TableColumn,
    Text,
    block_from_dict,
    inline_from_dict,
)


def test_document_round_trip():
    document = Document(
        header=Header(role="info", title="Hello"),
        blocks=[
            Paragraph(
                text=[
                    InlineText(text="hello "),
                    InlineStrong(children=[InlineText(text="world")]),
                    InlineLink(href="http://x", children=[InlineText(text="link")]),
                ]
            ),
            Heading(level=2, text=[InlineText(text="Section")]),
        ],
    )

    restored = Document.from_dict(document.to_dict())

    assert restored.header.role == document.header.role
    assert restored.header.title == document.header.title
    first = restored.blocks[0]
    assert isinstance(first, Paragraph)
    assert first.text[1].type == "strong"
    assert isinstance(first.text[1], InlineStrong)
    assert isinstance(first.text[1].children[0], InlineText)
    assert first.text[1].children[0].text == "world"


def test_block_union_dispatch_round_trip():
    source = Paragraph(text=[InlineText(text="p")])

    data = source.to_dict()
    restored = block_from_dict(data)

    assert isinstance(restored, Paragraph)
    assert restored.to_dict() == data


def test_inline_union_dispatch_all_types():
    inlines = [
        InlineText(text="t"),
        InlineStrong(children=[InlineText(text="s")]),
        InlineEm(children=[InlineText(text="e")]),
        InlineUnderline(children=[InlineText(text="u")]),
        InlineCode(children=[InlineText(text="c")]),
        InlineLink(href="h", children=[InlineText(text="l")]),
        InlineCmd(command="x", children=[InlineText(text="x")]),
        InlineArg(children=[InlineText(text="a")]),
        InlineMark(variant="x", children=[InlineText(text="m")]),
        InlineSelect(value="v", children=[InlineText(text="v")]),
        InlineSpace(count=2),
        InlineBreak(count=1),
    ]

    for inline in inlines:
        data = inline.to_dict()
        restored = inline_from_dict(data)
        assert type(restored) is type(inline), inline.type
        assert restored.to_dict() == data


def test_block_union_dispatch_all_types():
    blocks = [
        Text(text=[InlineText(text="t")]),
        Paragraph(text=[InlineText(text="p")]),
        Heading(level=3, text=[InlineText(text="h")]),
        Pre(code="code", language="py"),
        Rule(style="dashed"),
        Spacer(size=2),
        List(
            items=[ListItem(text=[InlineText(text="li")], blocks=[Paragraph(text=[])])]
        ),
        Kv(items=[KvItem(key="k", value=[InlineText(text="v")])]),
        Table(
            columns=[TableColumn(key="a", title="A")],
            rows=[["1", "2"]],
            variant="compact",
            selectable=False,
        ),
        Fields(name="f", fields=[Field(key="x", policy="text")]),
        Actions(actions=[Action(label="Go", command="go")]),
        Section(blocks=[Paragraph(text=[InlineText(text="s")])]),
        Stack(blocks=[Paragraph(text=[InlineText(text="s")])]),
        Flow(blocks=[Paragraph(text=[InlineText(text="f")])]),
        Collapsible(title=[InlineText(text="t")], expanded=True, blocks=[]),
        Image(ref="r", src="s", alt="a"),
    ]

    for block in blocks:
        data = block.to_dict()
        restored = block_from_dict(data)
        assert type(restored) is type(block), block.type
        assert restored.to_dict() == data


def test_to_dict_skips_none_and_empty():
    heading = Heading(level=1, text=[])
    data = heading.to_dict()
    assert data == {"type": "heading", "level": 1}


def test_from_dict_coerces_nested_block_unions():
    data = {
        "type": "section",
        "blocks": [
            {"type": "paragraph", "text": [{"type": "text", "text": "x"}]},
            {"type": "heading", "level": 2, "text": [{"type": "text", "text": "y"}]},
        ],
    }

    restored = block_from_dict(data)

    assert isinstance(restored, Section)
    assert isinstance(restored.blocks[0], Paragraph)
    assert isinstance(restored.blocks[1], Heading)


def test_block_from_dict_unknown_type_raises():
    with pytest.raises(ValueError, match="unknown block type"):
        block_from_dict({"type": "nope"})


def test_inline_from_dict_unknown_type_raises():
    with pytest.raises(ValueError, match="unknown inline type"):
        inline_from_dict({"type": "nope"})
