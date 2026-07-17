"""Example: access runtime context and ports via y5n SDK."""

from y5n.sdk import context, ports

ctx = context.current()
print(f"Path:    {ctx.path}")
print(f"Args:    {(ctx.request or {}).get('args', [])}")
print(f"Session: {(ctx.session or {}).get('key', '-')}")
print()

ports.register("hello", {"greet": lambda name="World": f"Hello, {name}!"})
hello = ports.get("hello")
print(hello.greet())
print(hello.greet(name="Yakoon"))
