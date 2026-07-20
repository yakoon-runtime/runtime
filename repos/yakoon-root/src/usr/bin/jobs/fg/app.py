from y5n.sdk import context, runtime


async def main():
    req = context.request()
    index = req.arg(0)

    flows = await runtime.scheduler.flows()
    try:
        idx = int(index)
    except (ValueError, TypeError):
        await runtime.io.write(f"Invalid index: {index}")
        return

    target = next((f for f in flows if f["index"] == idx), None)
    if not target:
        await runtime.io.write(f"Job {index} not found.")
        return

    await runtime.scheduler.foreground(target["id"])
    await runtime.io.write(f"Job {index} moved to foreground.")
