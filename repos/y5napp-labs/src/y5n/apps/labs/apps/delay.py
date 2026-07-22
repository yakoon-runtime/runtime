from y5n.sdk import io, timer


async def main():
    await io.write("Wait for 3 seconds\n...")
    await timer.delay(3)
    await io.write("One moment...")
    await timer.delay(2)
    await io.write("Done!", mode="replace")
