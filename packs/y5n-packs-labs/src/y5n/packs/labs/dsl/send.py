from y5n.sdk import io


async def main():
    await io.send("form.result", {"name": "test"})
    event = await io.receive("form.result")
    await io.write(f"Payload: {event.payload}")
