from y5n.sdk import runtime


async def main():
    await runtime.io.write("Hello write!")
