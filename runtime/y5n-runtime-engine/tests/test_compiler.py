"""Compiler -> normalize pipeline tests.

Covers the full document lifecycle up to the transport boundary:
  YDF markup -> Compiler.compile -> normalize() -> canonical document
"""

from __future__ import annotations

from y5n.runtime.api.document.normalize import normalize
from y5n.runtime.engine.wire.document import build_document_stack

SAMPLE = """<heading>Status</heading>

<paragraph>
  The service is <strong>online</strong> since <code>12:00</code>.
</paragraph>

<rule/>

<list>
  <item>alpha</item>
  <item>beta</item>
</list>

<kv>
  <item key="name">yakoon</item>
  <item key="version">1.0</item>
</kv>

<table selectable="false">
  <column key="a" title="A"/>
  <column key="b" title="B"/>
  <row><cell>1</cell><cell>2</cell></row>
</table>

<collapsible title="Details">
  <paragraph>more</paragraph>
</collapsible>
"""


def _compile(text: str = SAMPLE) -> dict:
    stack = build_document_stack()
    return stack.compiler.compile(text=text, context={})


def test_compiler_produces_document_dict():
    document = _compile()
    assert document["kind"] == "document"
    assert "blocks" in document
    assert document["blocks"]


def test_normalize_stamps_id_and_header():
    document = normalize(_compile())
    assert document["id"]
    assert document["id"].startswith("doc.")
    assert document["header"] is not None
    assert "role" in document["header"]


def test_normalize_assigns_unique_block_ids():
    document = normalize(_compile())
    blocks = document["blocks"]
    ids = [b["id"] for b in blocks]
    assert all(ids)
    assert len(ids) == len(set(ids))
    assert all(b["type"] for b in blocks)


def test_normalize_is_idempotent():
    once = normalize(_compile())
    twice = normalize(once)
    assert once == twice


def test_normalize_handles_missing_header():
    document = normalize({"kind": "document", "blocks": []})
    assert document["header"] == {"role": "info"}


def test_normalize_handles_missing_blocks():
    document = normalize({"kind": "document", "header": {"role": "error"}})
    assert document["blocks"] == []
    assert document["header"]["role"] == "error"


def test_compiler_pipeline_round_trip_matches_normalize():
    stack = build_document_stack()
    document = stack.compiler.compile(text=SAMPLE, context={})
    normalized = normalize(document)
    for block in normalized["blocks"]:
        assert block["id"]
        assert block["type"]


def test_whitespace_collapsed_outside_preserve_tags():
    document = _compile()
    normalized = normalize(document)
    assert normalized["blocks"][0]["type"] == "heading"
    assert normalized["blocks"][1]["type"] == "paragraph"
    text = normalized["blocks"][1]["text"]
    assert text[0]["type"] == "text"
    assert " " not in text[0]["text"][:2]
