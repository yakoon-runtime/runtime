from y5n.api.dsl.patterns import Form
from y5n.api.dsl.policies import IntPolicy
from y5n.api.invocations import Param


async def run(_):

    form = Form(
        title="Example Form",
        fields=[
            Param(key="first_name", title="Vorname"),
            Param(key="last_name", title="Nachname"),
            Param(key="age", title="Alter", policy=IntPolicy(min=1, max=99)),
        ],
    )

    async for outcome in form.run():
        yield outcome
