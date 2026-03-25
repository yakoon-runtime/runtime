import asyncio

from yakoon.base.interations import ConsoleInteraction
from yakoon.base.runtime.input import InputEvent
from yakoon.base.transports import Transport
from yakoon.base.ui import ViewDocument, ViewEvent
from yakoon.console.output import ConsoleOutput
from yakoon.console.ui import TerminalSurface, TerminalUI


class ConsoleClient:

    def __init__(self, transport: Transport):
        self.transport = transport

        # Form State
        self._current_fields = []
        self._current_index = 0
        self._current_values = {}

        # NEW: Single Source of Truth
        self.document = ViewDocument()

    async def run(self):

        async def cancel() -> None:
            await connection.send_input(InputEvent("__cancel__"))

        async def submit(event: InputEvent) -> None:

            raw = event.raw

            # ------------------------
            # Command Mode
            # ------------------------
            if not self._current_fields:
                await connection.send_input(InputEvent(raw))
                return

            # ------------------------
            # Form Mode
            # ------------------------
            if self._current_index >= len(self._current_fields):
                self._reset_form()
                return

            field = self._current_fields[self._current_index]

            self._current_values[field.var] = raw
            self._current_index += 1

            # nächstes Feld anzeigen
            if self._current_index < len(self._current_fields):
                self._show_next_prompt(ui)
                return

            # fertig → dict senden
            await connection.send_input(InputEvent(self._current_values))

        surface = TerminalSurface()
        renderer = ConsoleOutput(surface)
        ui = TerminalUI(
            surface,
            on_cancel=cancel,
            on_submit=submit,
        )

        interaction = ConsoleInteraction(ui)

        async def on_view(event: ViewEvent):

            # ------------------------
            # Document aktualisieren (zentral!)
            # ------------------------
            self.document.apply(event)

            # ------------------------
            # Rendern
            # ------------------------
            await renderer.view(event)

            if not event.is_final():
                return

            self._handle_view_ready(ui)

        connection = await self.transport.connect(on_emit=on_view)

        async with asyncio.TaskGroup() as tg:
            tg.create_task(renderer.run())
            tg.create_task(ui.run())

        await interaction.exit()

    # --------------------------------------------------------
    # View Ready
    # --------------------------------------------------------

    def _handle_view_ready(self, ui):

        self._reset_form()

        if not self.document.expects_input():
            ui.reset_prompt()
            return

        # Fields direkt aus Document
        self._current_fields = self.document.get_fields()
        self._current_index = 0
        self._current_values = {}

        if not self._current_fields:
            ui.reset_prompt()
            return

        self._show_next_prompt(ui)

    # --------------------------------------------------------
    # Prompt
    # --------------------------------------------------------

    def _show_next_prompt(self, ui):

        if self._current_index >= len(self._current_fields):
            return

        field = self._current_fields[self._current_index]

        ui.set_prompt(field)

    # --------------------------------------------------------
    # Helpers
    # --------------------------------------------------------

    def _reset_form(self):
        self._current_fields = []
        self._current_index = 0
        self._current_values = {}
