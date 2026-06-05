from __future__ import annotations

from pathlib import Path

from y5ncli.console.client.terminal import Terminal

from textual.app import App, ComposeResult
from textual.widgets import Input, RichLog


class _InnerApp(App):

    CSS_PATH = Path(__file__).parent / "terminal.tcss"

    def __init__(self, terminal: TextualTerminal):
        super().__init__()
        self._terminal = terminal
        self.output: RichLog | None = None
        self.input: Input | None = None

    def compose(self) -> ComposeResult:
        self.output = RichLog(highlight=True, markup=False, wrap=True)
        self.input = Input(placeholder="shell$ ")
        yield self.output
        yield self.input

    async def on_input_submitted(self, message: Input.Submitted) -> None:
        text = message.value

        assert self.input
        self.input.clear()
        await self._terminal.on_input(text)


class TextualTerminal(Terminal):

    def __init__(self):
        self._app = _InnerApp(self)

    async def run(self):
        await self._app.run_async()

    async def stop(self):
        self._app.exit()

    async def on_input(self, text: str):
        pass

    def write(self, text: str):
        if self._app.output:
            self._app.output.write(text)

    def new_line(self):
        if self._app.output:
            self._app.output.write("")

    def set_prompt(self, text: str):
        if self._app.input:
            self._app.input.placeholder = text
