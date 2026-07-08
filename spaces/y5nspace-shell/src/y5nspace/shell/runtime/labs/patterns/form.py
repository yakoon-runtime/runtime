from y5n.api.dsl.patterns import Form
from y5n.api.dsl.policies import IntPolicy
from y5n.api.invocations import Param


async def run(_):

    initial = {}
    initial["first_name"] = "stefan"

    form = Form(
        title="Example Form",
        fields=[
            Param(key="first_name", title="Vorname"),
            Param(key="last_name", title="Nachname", required=True),
            Param(key="age", title="Alter", policy=IntPolicy(min=1, max=99)),
            Param(key="street", title="Straße", required=True),
        ],
        initial=initial,
        focus="last_name",
    )

    async for outcome in form.run():
        yield outcome
