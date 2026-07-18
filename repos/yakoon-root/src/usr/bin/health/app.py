from y5n.api.dsl import out
from y5n.api.nodes import NodeSpace
from y5n.base.ports.models import HealthLevel
from y5n.base.ports.system import VALIDATE


async def run(space: NodeSpace):
    validate = space.ports.get(VALIDATE)
    if validate is None:
        yield out({
            "kind": "document",
            "header": {"role": "info"},
            "blocks": [
                {"type": "heading", "level": 1, "text": [{"type": "text", "text": "No VALIDATE port available"}]}
            ],
        })
        return

    result = validate()

    total = len(result.children)
    healthy = sum(1 for c in result.children if c.level == HealthLevel.GREEN)
    errors_count = sum(1 for c in result.children if c.level == HealthLevel.RED)
    warnings = sum(1 for c in result.children if c.level == HealthLevel.YELLOW)

    kv_items = [
        {"type": "kv_item", "key": "Healthy", "value": [{"type": "text", "text": str(healthy)}]},
        {"type": "kv_item", "key": "Errors", "value": [{"type": "text", "text": str(errors_count)}]},
        {"type": "kv_item", "key": "Warnings", "value": [{"type": "text", "text": str(warnings)}]},
    ]

    children_blocks = []
    for child in result.children:
        icon = {
            HealthLevel.GREEN: "\u2713",
            HealthLevel.YELLOW: "\u26a0",
            HealthLevel.RED: "\u2717",
        }.get(child.level, "?")
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
    yield out(doc)
