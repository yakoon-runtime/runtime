import asyncio

from prompt_toolkit.application import Application
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import HSplit, Layout, Window
from prompt_toolkit.widgets import TextArea


class TerminalUI:

    def __init__(self, surface, on_cancel):

        self.surface = surface
        self.on_cancel = on_cancel

        self._prompt = "shell$ "
        self._future: asyncio.Future | None = None

        self.history = InMemoryHistory()

        self.view = TextArea(
            text="",
            scrollbar=True,
            focusable=True,
            wrap_lines=True,
        )

        self.shell = TextArea(
            height=1,
            prompt=lambda: self._prompt,
            multiline=False,
            wrap_lines=False,
            history=self.history,
        )
        self.shell.accept_handler = self._on_enter

        kb = KeyBindings()

        @kb.add("pageup")
        def _(event):
            self.view.buffer.cursor_up(count=5)

        @kb.add("pagedown")
        def _(event):
            self.view.buffer.cursor_down(count=5)

        @kb.add("c-c")
        def _(event):
            if self.on_cancel:
                asyncio.create_task(self.on_cancel())
            self.app.exit()

        root = HSplit(
            [
                self.shell,
                Window(height=1, char="─"),
                self.view,
            ]
        )

        self.app = Application(
            layout=Layout(root),
            full_screen=True,
            mouse_support=True,
            key_bindings=kb,
        )

        self.surface.attach(self.view.buffer, self.app)

    async def run(self):
        await self.app.run_async()

    async def stop(self):
        try:
            if self.app.is_running:
                self.app.exit()
        except Exception:
            pass

    async def read_line(self, prompt: str):

        self._prompt = prompt
        self.app.invalidate()

        loop = asyncio.get_running_loop()
        self._future = loop.create_future()

        try:
            return await self._future
        except asyncio.CancelledError:
            return ""

    def _on_enter(self, buffer):
        if not buffer.text:
            return

        text = buffer.text
        buffer.text = ""

        self.surface.new_view()

        if self._future and not self._future.done():
            self._future.set_result(text)

    def add_history(self, command: str):
        self.history.append_string(command)
