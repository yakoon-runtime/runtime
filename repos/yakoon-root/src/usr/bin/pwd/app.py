from y5n.sdk import context


async def main():
    ctx = context.current()

    display = ctx.cwd
    if not display:
        display = ctx.workspace or "/"

    print(display)
