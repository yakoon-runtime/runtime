from uuid import uuid4

from y5n.api.dsl import out_text, receive, start_task
from y5n.base.flow.channel import Scope


async def run(_):
    """
    Labs: Tasks

    Demonstrates:

    - starting real OS processes
    - receiving results through channels
    - waiting for task completion
    - running tasks in parallel
    """

    lines: list[str] = []

    def render():
        return out_text("\n".join(lines))

    # ------------------------------------------------------------------
    # Example 1: Real OS process
    # ------------------------------------------------------------------

    lines.append("Example 1: Execute a real OS process")
    lines.append("")
    yield render()

    lines.append("→ starting: python3 -c 'print(42)'")
    yield render()

    ch = uuid4().hex
    yield start_task("python3", result_channel=ch, args=["-c", "print(42)"])

    lines.append("→ waiting for process result...")
    yield render()

    result = yield receive(ch, scope=Scope.SESSION)
    payload = result.payload or {}

    lines.append("→ process completed")
    lines.append(f"→ returncode={payload.get('returncode')}")
    lines.append(f"→ stdout={payload.get('stdout', '').strip()}")
    yield render()

    lines.append("")
    lines.append("---")
    lines.append("")
    yield render()

    # ------------------------------------------------------------------
    # Example 2: Parallel tasks
    # ------------------------------------------------------------------

    lines.append("Example 2: Parallel execution")
    lines.append("")
    yield render()

    ch_a = uuid4().hex
    ch_b = uuid4().hex

    yield start_task("sleep", result_channel=ch_a, seconds=3)
    yield start_task("sleep", result_channel=ch_b, seconds=5)

    lines.append("→ both tasks are now running in parallel")
    yield render()

    lines.append("")
    lines.append("→ waiting for task A...")
    yield render()

    result_a = yield receive(ch_a, scope=Scope.SESSION)
    lines.append(f"→ task A completed: {result_a.payload}")
    yield render()

    lines.append("")
    lines.append("→ waiting for task B...")
    yield render()

    result_b = yield receive(ch_b, scope=Scope.SESSION)
    lines.append(f"→ task B completed: {result_b.payload}")

    lines.append("")
    lines.append("→ all tasks completed")
    yield render()
