from y5n.api.dsl import out_text
from y5n.api.dsl.patterns import Form


async def run(_):

    form = Form()

    yield form.ask(
        key="first_name",
        title="Vorname:",
    )

    yield form.ask(
        key="last_name",
        title="Nachname:",
    )

    yield out_text(str(form.data))
