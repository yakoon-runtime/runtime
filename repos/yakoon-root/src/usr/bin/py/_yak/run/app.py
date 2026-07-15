import asyncio
import sys


async def main():

    args = sys.argv[1:]
    for i in range(5):
        if args:
            print(f"{' '.join(args)} — Tick {i}")
        else:
            print(f"Tick {i}")
        sys.stdout.flush()
        await asyncio.sleep(2)


asyncio.run(main())
