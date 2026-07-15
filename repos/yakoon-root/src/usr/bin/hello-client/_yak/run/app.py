"""Consumes a port service from the runtime."""

from y5n.sdk import ports

hello = ports.get("hello")
print(hello.greet())
print(hello.greet(name="Yakoon"))
