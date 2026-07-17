"""Registers a port service in the runtime."""

from y5n.sdk import ports


class Greeter:
    def greet(self, name="World"):
        return f"Hello, {name}!"


def main():
    ports.promote("hello", Greeter())
    print("service 'hello' registered")
