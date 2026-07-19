from y5n.sdk import context, ports, runtime


async def main():
    flows_service = ports.get("jobs.list")
    flows = await flows_service.get(
        session_key=context.session().key,
        exclude_id=context.flow().id,
    )

    if not flows:
        await runtime.write("No jobs active.")
        return

    await runtime.write("Active jobs:", mode="append")

    focused = context.current().node.get("path", "")
    for entry in flows:
        marker = "  ←" if entry.get("id", "") == focused else ""
        await runtime.write(
            f"  [{entry['index']}] {entry['label']} - {entry['state']}{marker}",
            mode="append",
        )
