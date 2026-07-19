from y5n.sdk import runtime


async def main():
    await runtime.write("Wait for 3 seconds\n...")
    await runtime.delay(3)
    await runtime.write("One moment...")
    await runtime.delay(2)
    await runtime.write("Done!", mode="replace")
