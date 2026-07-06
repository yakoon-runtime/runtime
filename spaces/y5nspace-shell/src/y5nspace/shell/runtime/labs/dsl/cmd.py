from uuid import uuid4

from y5n.api.dsl import out_text, receive, start_cmd
from y5n.base.flow.channel import Scope


async def run(_):
    lines: list[str] = []

    def render():
        return out_text("\n".join(lines))

    lines.append("Example: start_cmd")
    lines.append("")
    yield render()

    result_channel = f"cmd:{uuid4().hex}"
    yield start_cmd("out", channel=result_channel)

    lines.append("→ waiting for projection from sub-flow...")
    yield render()

    ev = yield receive(result_channel, scope=Scope.SESSION)
    lines.append(f"→ received: {ev.payload!r}")
    yield render()

    lines.append("")
    lines.append("---")
    yield render()
