from y5n.sdk import ports, runtime
from y5n.sdk.models import (
    Collapsible,
    Document,
    Header,
    Heading,
    InlineText,
    Kv,
    KvItem,
    Rule,
    Spacer,
    Text,
)


async def main():
    validate = ports.get("validate")
    result = await validate()

    total = len(result.children)
    healthy = sum(1 for c in result.children if c.level.value == "green")
    errors_count = sum(1 for c in result.children if c.level.value == "red")
    warnings = sum(1 for c in result.children if c.level.value == "yellow")

    icons = {"green": "\u2713", "yellow": "\u26a0", "red": "\u2717"}
    children_blocks = [
        Text(
            text=[
                InlineText(
                    text=f"  {icons.get(child.level.value, '?')} {child.message or ''}"
                )
            ]
        )
        for child in result.children
    ]

    doc = Document(
        header=Header(role="info"),
        blocks=[
            Heading(level=1, text=[InlineText(text="Health")]),
            Rule(),
            Collapsible(
                title=[InlineText(text=f"Tree validation ({total})")],
                expanded=False,
                blocks=children_blocks,
            ),
            Spacer(size=1),
            Kv(
                items=[
                    KvItem(key="Healthy", value=[InlineText(text=str(healthy))]),
                    KvItem(key="Errors", value=[InlineText(text=str(errors_count))]),
                    KvItem(key="Warnings", value=[InlineText(text=str(warnings))]),
                ]
            ),
        ],
    )
    await runtime.io.write(doc)
