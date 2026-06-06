from y5n.api.dsl import out_text, receive, run_task


async def run(_):
    """
    Labs: Tasks

    Demonstrates:

    - starting real OS processes
    - receiving results through channels
    - waiting for task completion
    - running tasks in parallel

    Tasks integrate into the existing flow/event model and do not
    require a separate scheduler or execution model.
    """

    lines: list[str] = []

    def render():
        return out_text("\n".join(lines))

    # ------------------------------------------------------------------
    # Example 1
    #
    # Start a real OS process and wait for its result.
    #
    # Flow
    #   ↓
    # run_task(...)
    #   ↓
    # OS Process
    #   ↓
    # Event
    #   ↓
    # receive(channel)
    #   ↓
    # Flow
    # ------------------------------------------------------------------

    lines.append("Example 1: Execute a real OS process")
    lines.append("")
    yield render()

    lines.append("→ starting: python3 -c 'print(42)'")
    yield render()

    task = run_task(
        "python3",
        args=["-c", "print(42)"],
    )

    # Launch the process.
    yield task

    lines.append("→ waiting for process result...")
    yield render()

    # Suspend until the task sends an event to its channel.
    result = yield receive(task.channel)

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
    # Example 2
    #
    # Start two independent tasks in parallel.
    #
    # Both tasks are launched immediately.
    #
    # Expected runtime:
    #     ~5 seconds
    #
    # Not:
    #     3 + 5 = 8 seconds
    #
    # This demonstrates that tasks execute independently from the flow
    # and communicate exclusively through channels.
    # ------------------------------------------------------------------

    lines.append("Example 2: Parallel execution")
    lines.append("")
    yield render()

    task_a = run_task("sleep", seconds=3)
    task_b = run_task("sleep", seconds=5)

    lines.append("→ starting task A (3s)")
    yield render()
    yield task_a

    lines.append("→ starting task B (5s)")
    yield render()
    yield task_b

    lines.append("")
    lines.append("→ both tasks are now running in parallel")
    yield render()

    lines.append("")
    lines.append("→ waiting for task A...")
    yield render()

    result_a = yield receive(task_a.channel)

    lines.append(f"→ task A completed: {result_a.data}")
    yield render()

    lines.append("")
    lines.append("→ waiting for task B...")
    yield render()

    result_b = yield receive(task_b.channel)

    lines.append(f"→ task B completed: {result_b.data}")

    lines.append("")
    lines.append("→ all tasks completed")
    yield render()
