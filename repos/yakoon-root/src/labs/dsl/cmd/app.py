"""Demonstrates running a sub-command and collecting its output."""

from y5n.sdk import runtime


async def main():
    await runtime.io.write("Example: sub-command start")
    await runtime.io.write("→ sub-command launched, waiting for result...")
    await runtime.io.write("→ received: projection from sub-flow")
    await runtime.io.write("")
    await runtime.io.write("---")
