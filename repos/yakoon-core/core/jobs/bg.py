from y5n.sdk import io, scheduler


async def main():
    result = await scheduler.background()

    if result is None:
        await io.write("No job in foreground.")
        return

    await io.write("Job moved to background.")
