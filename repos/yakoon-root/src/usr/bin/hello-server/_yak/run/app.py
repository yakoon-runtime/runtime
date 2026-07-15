"""Registers a port service in the runtime."""

from y5n.sdk import ports

ports.register("hello", {"greet": lambda name="World": f"Hello, {name}!"})

print("service 'hello' registered")
