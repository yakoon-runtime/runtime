from y5n.sdk import context, runtime


async def main():
    req = context.request()

    if req.has_option("current"):
        flows = await runtime.scheduler.flows()
        fg = next((f for f in flows if f.get("foreground")), None)
        if not fg:
            await runtime.io.write("No job in foreground.")
            return
        await runtime.scheduler.stop(fg["id"])
        await runtime.io.write("Job was stopped.")
        return

    index = req.arg(0)
    flows = await runtime.scheduler.flows()
    try:
        idx = int(index)
    except ValueError:
        await runtime.io.write(f"Invalid index: {index}")
        return

    target = next((f for f in flows if f["index"] == idx), None)
    if not target:
        await runtime.io.write(f"Job {index} not found.")
        return

    await runtime.scheduler.stop(target["id"])
    await runtime.io.write(f"Job {index} was stopped.")
