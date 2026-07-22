from y5n.sdk import context, io, session


async def main():
    target = context.request().arg(0)
    if not target:
        await io.write("Usage: session attach <key>")
        return

    await session.attach(target)
    await io.write(f"Attached to session {target}")
