from y5n.base.flow.dsl import out_text, prompt, receive, to_text
from y5n.base.flow.policies import BasePolicy, ValidationError


class Form:

    def __init__(self):
        self.data = {}

    async def ask(
        self,
        key: str,
        title: str,
        policy: BasePolicy | None = None,
    ):

        while True:

            yield prompt(to_text(title))
            event = yield receive()

            try:

                if policy:
                    value = policy.validate(event.data)
                else:
                    value = event.data

                self.data[key] = value
                break

            except ValidationError as e:
                yield out_text(e.args[0])
