"""Example: access runtime context via y5n SDK."""

from y5n.sdk import context

ctx = context.current()
print(f"Path:    {ctx.path}")
print(f"Args:    {(ctx.request or {}).get('args', [])}")
print(f"Session: {(ctx.session or {}).get('key', '-')}")
