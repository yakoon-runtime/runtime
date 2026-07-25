from y5n.sdk import context, runtime


async def main():
    flows = await runtime.scheduler.flows()

    if not flows:
        await runtime.io.write("No jobs active.")
        return

    await runtime.io.write("Active jobs:", mode="append")

    focused = context.current().node.get("path", "")
    for entry in flows:
        marker = "  ←" if entry.get("id", "") == focused else ""
        await runtime.io.write(
            f"  [{entry['index']}] {entry['label']} - {entry['state']}{marker}",
            mode="append",
        )
