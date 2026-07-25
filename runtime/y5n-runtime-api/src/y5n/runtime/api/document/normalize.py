"""Document normalizer — ensures every document is canonical.

Responsibilities:
  - Assign unique IDs to blocks that lack them
  - Set default header if missing
  - Ensure tree structure is valid

After normalize(), every block has an id, every doc has a header,
and the document is ready for the transport layer.
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence

from .schema import CHILDREN_FIELDS


def normalize(doc: dict) -> dict:
    """Produce a canonical document dict.

    Input may be a partial document (no ids, no header).
    Output always has:
      - ``id``  (document-level)
      - ``header`` with at least ``role``
      - ``blocks`` each with ``id``, ``type``
    """
    doc_id = doc.get("id") or _make_doc_id()

    if doc.get("header") is None:
        doc["header"] = {"role": "info"}

    blocks = list(_assign_ids(doc_id, doc.get("blocks", [])))

    return {
        "id": doc_id,
        "kind": "document",
        "header": doc.get("header"),
        "blocks": blocks,
    }


def _make_doc_id() -> str:
    return f"doc.{uuid.uuid4().hex}"


def _assign_ids(parent_path: str, blocks: Sequence[dict]) -> list[dict]:
    result = []
    for i, block in enumerate(blocks):
        block = dict(block)
        block_path = f"{parent_path}.{i}"
        if not block.get("id"):
            block["id"] = block_path
        children_field = CHILDREN_FIELDS.get(block.get("type", ""))
        if children_field and block.get(children_field):
            block[children_field] = _assign_ids(block_path, block[children_field])
        result.append(block)
    return result
