from y5n.sdk import runtime


async def main():
    for i in range(15):
        await runtime.io.write(f"tick-{i}")
        await runtime.timer.delay(2)
