from y5n.sdk import runtime


async def main():
    result = await runtime.scheduler.background()

    if result is None:
        await runtime.io.write("No job in foreground.")
        return

    await runtime.io.write("Job moved to background.")
