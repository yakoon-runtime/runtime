from y5n.runtime.api.dsl.patterns import Form
from y5n.runtime.api.dsl.policies import IntPolicy


async def run(_):
    form = Form(title="Example Dialog")

    yield form.ask("first_name", "Vorname")
    yield form.ask("last_name", "Nachname")
    yield form.ask("age", "Alter", policy=IntPolicy(min=1, max=99))
