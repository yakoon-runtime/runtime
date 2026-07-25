from __future__ import annotations


def to_text(text: str) -> dict:
    if not text:
        return {"kind": "document", "header": {"role": "info"}, "blocks": []}
    return {
        "kind": "document",
        "header": {"role": "info"},
        "blocks": [
            {
                "type": "text",
                "text": [{"type": "text", "text": text}],
            }
        ],
    }
