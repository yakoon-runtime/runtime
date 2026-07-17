"""Consumes a port service from the runtime."""

from y5n.sdk import ports


async def main():
    hello = ports.get("hello")
    print(await hello.greet())
    print(await hello.greet(name="Yakoon"))
