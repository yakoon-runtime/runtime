from y5n.base.flow.dsl import prompt, receive, to_text


class Form:

    def __init__(self):
        self.data = {}

    async def ask(self, key: str, title: str):

        yield prompt(to_text(title))
        event = yield receive()

        self.data[key] = event.data
