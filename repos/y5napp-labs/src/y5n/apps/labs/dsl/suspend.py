"""Demonstrates self-suspend — flow pauses, resumes via 'jobs fg'."""

from y5n.sdk import io
from y5n.sdk.scheduler import scheduler


async def main():
    await scheduler.foreground()

    await io.write("Vorname:")
    event = await io.receive()
    await io.write(f"Result Vorname: {event.payload}")

    await io.write("see 'jobs'")
    await scheduler.suspend()

    await io.write("Nachname:")
    event = await io.receive()
    await io.write(f"Result Nachname: {event.payload}")
