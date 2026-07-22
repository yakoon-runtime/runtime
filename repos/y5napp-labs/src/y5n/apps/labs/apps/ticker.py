from y5n.sdk import io, timer


async def main():
    for i in range(15):
        await io.write(f"tick-{i}")
        await timer.delay(2)
