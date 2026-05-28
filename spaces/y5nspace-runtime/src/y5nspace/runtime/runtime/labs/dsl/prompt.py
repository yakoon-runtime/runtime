from y5n.api.flows import foreground, out, prompt, receive
from y5n.api.projections import to_text


async def run(_):

    yield foreground()

    yield prompt(to_text("Vorname:"))
    first_Name = yield receive()

    yield prompt(to_text("Nachname:"))
    last_Name = yield receive()

    yield out(to_text("\nEingabe:"))
    yield out(to_text(f"{first_Name.data}, {last_Name.data}"))
