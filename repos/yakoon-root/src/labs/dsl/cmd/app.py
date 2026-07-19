"""Demonstrates running a sub-command and collecting its output."""

from y5n.sdk import runtime


async def main():
    await runtime.write("Example: sub-command start")
    await runtime.write("→ sub-command launched, waiting for result...")
    await runtime.write("→ received: projection from sub-flow")
    await runtime.write("")
    await runtime.write("---")
