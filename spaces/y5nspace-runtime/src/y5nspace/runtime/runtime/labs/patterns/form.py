from y5n.api.dsl import out_text
from y5n.api.dsl.patterns import Form
from y5n.api.dsl.policies import IntPolicy


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

    # you can use subflows
    yield ask_age(form)

    yield out_text(str(form.data))


async def ask_age(form):

    yield form.ask(
        key="age",
        title="Alter:",
        policy=IntPolicy(min=1, max=99),
    )
