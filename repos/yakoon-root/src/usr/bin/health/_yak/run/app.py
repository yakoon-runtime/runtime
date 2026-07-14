from y5n.api.dsl import out
from y5n.api.nodes import NodeSpace
from y5n.base.ports.models import HealthLevel
from y5n.base.ports.system import VALIDATE
from y5n.base.projection.model.block import (
    CollapsibleBlock,
    HeadingBlock,
    InlineText,
    KvBlock,
    KvItemBlock,
    RuleBlock,
    SpacerBlock,
    TextBlock,
)
from y5n.base.projection.model.model import Projection


async def run(space: NodeSpace):
    validate = space.ports.get(VALIDATE)
    if validate is None:
        yield out(
            Projection.create(
                blocks=[
                    HeadingBlock(
                        level=1, text=[InlineText("text", "No VALIDATE port available")]
                    )
                ]
            )
        )
        return

    result = validate()

    total = len(result.children)
    healthy = sum(1 for c in result.children if c.level == HealthLevel.GREEN)
    errors = sum(1 for c in result.children if c.level == HealthLevel.RED)
    warnings = sum(1 for c in result.children if c.level == HealthLevel.YELLOW)

    kv_items = [
        KvItemBlock(key="Healthy", value=[InlineText("text", str(healthy))]),
        KvItemBlock(key="Errors", value=[InlineText("text", str(errors))]),
        KvItemBlock(key="Warnings", value=[InlineText("text", str(warnings))]),
    ]

    children_blocks = []
    for child in result.children:
        icon = {
            HealthLevel.GREEN: "\u2713",
            HealthLevel.YELLOW: "\u26a0",
            HealthLevel.RED: "\u2717",
        }.get(child.level, "?")
        children_blocks.append(TextBlock.create(text=f"  {icon} {child.message or ''}"))

    projection = Projection.create(
        blocks=[
            HeadingBlock(level=1, text=[InlineText("text", "Health")]),
            RuleBlock(),
            CollapsibleBlock(
                title=[InlineText("text", f"Tree validation ({total})")],
                expanded=False,
                blocks=children_blocks,
            ),
            SpacerBlock(),
            KvBlock(items=kv_items),
        ]
    )
    yield out(projection)
