from y5n.sdk import context, runtime


async def main():
    ctx = context.current()

    display = ctx.cwd
    if not display:
        display = ctx.workspace or "/"

    await runtime.write(display)
