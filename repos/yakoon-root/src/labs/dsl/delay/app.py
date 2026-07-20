from y5n.sdk import runtime


async def main():
    await runtime.io.write("Wait for 3 seconds\n...")
    await runtime.timer.delay(3)
    await runtime.io.write("One moment...")
    await runtime.timer.delay(2)
    await runtime.io.write("Done!", mode="replace")
