import shlex

from yakoon.base.runtime.input.event import InputEvent


class InputParser:

    def parse(self, event: InputEvent) -> tuple[InputEvent, list[str]]:

        parts = self.split_pipes(event.command)

        if not parts:
            return event, []

        # HEAD vorbereiten (für dispatch!)
        head = parts[0]
        tokens = shlex.split(head)

        event = InputEvent(
            command=tokens[0],
            tokens=tokens[1:],
            payload=event.payload,
            context=event.context,
        )

        # Rest bleibt roh
        commands = parts[1:]

        return event, commands

    def split_pipes(self, raw: str) -> list[str]:
        parts = []
        current = []
        in_quotes = False
        quote_char = None

        for char in raw:
            if char in ('"', "'"):
                if in_quotes and char == quote_char:
                    in_quotes = False
                    quote_char = None
                elif not in_quotes:
                    in_quotes = True
                    quote_char = char

            if char == "|" and not in_quotes:
                parts.append("".join(current).strip())
                current = []
            else:
                current.append(char)

        if current:
            parts.append("".join(current).strip())

        return parts
