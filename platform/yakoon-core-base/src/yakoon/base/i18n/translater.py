class Translator:

    def __init__(
        self,
        messages: dict[str, dict[str, str]],
    ):
        self.messages = messages

    def translate(
        self,
        *,
        lang: str,
        code: str,
        data: dict,
    ) -> str:

        table = self.messages.get(lang, {})
        template = table.get(code)

        if not template:
            template = code

        return template.format(**data)
