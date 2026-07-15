"""Example: access runtime context via y5napi."""

from y5n.runtime.executor.napi import context

ctx = context.current()
print(f"Path:    {ctx.path}")
print(f"Args:    {ctx.request.args() if ctx.request else '-'}")
print(f"Session: {ctx.session.key if ctx.session else '-'}")
print(f"CWD:     {ctx.session.get_data('fs:root') if ctx.session else '-'}")
