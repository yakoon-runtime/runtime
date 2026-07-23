"""Demonstrates io.receive() — waits for user input, accepts two values."""

from y5n.sdk import io


async def main():
    await io.write("receive suspended in background... see 'jobs'")

    event1 = await io.receive()
    await io.write(f"Got: {event1.payload}")

    event2 = await io.receive()
    await io.write(f"Got: {event2.payload}")
