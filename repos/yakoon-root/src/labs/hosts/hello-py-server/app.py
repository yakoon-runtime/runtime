"""Registers a port service in the runtime."""

from y5n.sdk import ports, runtime


class Greeter:
    def greet(self, name="World"):
        return f"Hello, {name}!"


async def main():
    ports.promote("hello", Greeter())
    await runtime.io.write("service 'hello' registered")
