"""Consumes a port service from the runtime."""

from y5n.sdk import context, ports


async def main():
    hello = ports.get("hello")
    print(await hello.greet())
    print(await hello.greet(name="Yakoon"))

    ctx = context.current()
    print(f"\nrunning at: {ctx.node.get('path', '?')}")
    print(f"user: {ctx.user.get('name', ctx.user.get('id', '?'))}")
