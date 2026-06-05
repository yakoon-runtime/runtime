from y5n.base.flow.dsl import out_text, prompt, receive, to_text
from y5n.base.flow.policies import BasePolicy, ValidationError


class Form:

    def __init__(self):
        self.data: dict[str, str] = {}
        self._titles: dict[str, str] = {}
        self._error: str | None = None

    def _render(self, current_title: str = "") -> str:
        lines = []
        for key, value in self.data.items():
            label = self._titles.get(key, key.replace("_", " ").title())
            lines.append(f"{label}: {value}")
        if current_title:
            lines.append(current_title)
        if self._error:
            lines.append(f"  ! {self._error}")
        return "\n".join(lines)

    async def ask(
        self,
        key: str,
        title: str,
        policy: BasePolicy | None = None,
    ):

        while True:

            yield prompt(to_text(self._render(title)))
            event = yield receive()

            try:

                if policy:
                    result = policy.validate(event.data)
                else:
                    result = event.data

                value: str = result if result is not None else ""
                self.data[key] = value
                self._titles[key] = title.rstrip(": ")
                self._error = None
                yield out_text(self._render())
                break

            except ValidationError as e:
                self._error = e.args[0]
                yield prompt(to_text(self._render(title)))
