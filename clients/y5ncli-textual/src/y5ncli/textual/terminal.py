from __future__ import annotations

from y5ncli.console.client.terminal import Terminal

from textual.app import App, ComposeResult
from textual.widgets import Input, RichLog


class TextualTerminal(App, Terminal):

    CSS = """
    Screen {
        layout: vertical;
    }
    RichLog {
        height: 1fr;
    }
    Input {
        dock: bottom;
    }
    """

    def __init__(self):
        App.__init__(self)
        self._output: RichLog | None = None
        self._input: Input | None = None

    # ----------------------------------
    # Textual Lifecycle
    # ----------------------------------

    def compose(self) -> ComposeResult:
        self._output = RichLog(highlight=True, markup=False, wrap=True)
        self._input = Input(placeholder="shell$ ")
        yield self._output
        yield self._input

    async def on_input_submitted(self, message: Input.Submitted) -> None:
        text = message.value
        self._input.clear()
        await self.on_input(text)

    # ----------------------------------
    # Terminal API
    # ----------------------------------

    async def run(self):
        await self.run_async()

    async def stop(self):
        self.exit()

    async def on_input(self, text: str):
        pass

    def write(self, text: str):
        if self._output:
            self._output.write(text)

    def new_line(self):
        if self._output:
            self._output.write("")

    def set_prompt(self, text: str):
        if self._input:
            self._input.placeholder = text
