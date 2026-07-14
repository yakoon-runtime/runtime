from y5n.api.dsl import out_text
from y5n.api.nodes import NodeSpace
from y5n.base.ports.models import HealthLevel
from y5n.base.ports.system import VALIDATE


async def run(space: NodeSpace):
    validate = space.ports.get(VALIDATE)
    if validate is None:
        yield out_text("No VALIDATE port available")
        return

    result = validate()

    lines = [_icon(result.level) + " " + (result.message or "")]
    for child in result.children:
        lines.append("  " + _icon(child.level) + " " + (child.message or ""))

    errors = sum(1 for c in result.children if c.level == HealthLevel.RED)
    warnings = sum(1 for c in result.children if c.level == HealthLevel.YELLOW)
    if errors or warnings:
        parts = []
        if errors:
            parts.append(str(errors) + " error(s)")
        if warnings:
            parts.append(str(warnings) + " warning(s)")
        lines.append("")
        lines.append("  " + " / ".join(parts))

    yield out_text("\n".join(lines))


def _icon(level: HealthLevel) -> str:
    return {HealthLevel.GREEN: "\u2713", HealthLevel.YELLOW: "\u26A0", HealthLevel.RED: "\u2717"}.get(level, "?")
