from __future__ import annotations

import json

from y5n.base.projection.model import TableBlock


def map_table(mapper, node):
    headers_raw = node.attrs.get("headers", "[]")
    rows_raw = node.attrs.get("rows", "[]")

    try:
        headers = json.loads(headers_raw)
    except json.JSONDecodeError:
        raise ValueError(f"<table> headers is not valid JSON: {headers_raw!r}")

    try:
        rows = json.loads(rows_raw)
    except json.JSONDecodeError:
        raise ValueError(f"<table> rows is not valid JSON: {rows_raw!r}")

    if not isinstance(headers, list) or not all(isinstance(h, str) for h in headers):
        raise ValueError("<table> headers must be a list of strings")

    if not isinstance(rows, list) or not all(isinstance(r, list) for r in rows):
        raise ValueError("<table> rows must be a list of lists")

    return TableBlock(
        headers=headers,
        rows=rows,
    )
