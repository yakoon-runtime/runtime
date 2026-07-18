from y5n.sdk import ports


async def main():
    validate = ports.get("validate")
    result = await validate()

    total = len(result.children)
    healthy = sum(1 for c in result.children if c.level.value == "green")
    errors_count = sum(1 for c in result.children if c.level.value == "red")
    warnings = sum(1 for c in result.children if c.level.value == "yellow")

    kv_items = [
        {"type": "kv_item", "key": "Healthy", "value": [{"type": "text", "text": str(healthy)}]},
        {"type": "kv_item", "key": "Errors", "value": [{"type": "text", "text": str(errors_count)}]},
        {"type": "kv_item", "key": "Warnings", "value": [{"type": "text", "text": str(warnings)}]},
    ]

    children_blocks = []
    icons = {"green": "\u2713", "yellow": "\u26a0", "red": "\u2717"}
    for child in result.children:
        icon = icons.get(child.level.value, "?")
        children_blocks.append(
            {"type": "text", "text": [{"type": "text", "text": f"  {icon} {child.message or ''}"}]}
        )

    doc = {
        "kind": "document",
        "header": {"role": "info"},
        "blocks": [
            {"type": "heading", "level": 1, "text": [{"type": "text", "text": "Health"}]},
            {"type": "rule"},
            {
                "type": "collapsible",
                "title": [{"type": "text", "text": f"Tree validation ({total})"}],
                "expanded": False,
                "blocks": children_blocks,
            },
            {"type": "spacer", "size": 1},
            {"type": "kv", "items": kv_items},
        ],
    }
    print(doc)
