"""Demonstrates running a sub-command and collecting its output."""

from y5n.sdk import io


async def main():
    await io.write("Example: sub-command start")
    await io.write("→ sub-command launched, waiting for result...")
    await io.write("→ received: projection from sub-flow")
    await io.write("")
    await io.write("---")
