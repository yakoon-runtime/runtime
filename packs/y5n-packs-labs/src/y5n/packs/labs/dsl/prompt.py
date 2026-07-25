from y5n.sdk import io


async def main():
    event_fn = await io.prompt("Your firstname:")
    event_ln = await io.prompt("Your lastname:")
    await io.write(f"{event_fn}, {event_ln}")
