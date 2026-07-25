from y5n.sdk import io, session


async def main():
    await session.detach()
    await io.write("Detached")
