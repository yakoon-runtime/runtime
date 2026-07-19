from y5n.sdk import runtime


async def main():
    for i in range(15):
        await runtime.write(f"tick-{i}")
        await runtime.delay(2)
