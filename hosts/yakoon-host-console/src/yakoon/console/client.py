import asyncio

from yakoon.base.host import InputEvent
from yakoon.base.interations import ConsoleInteraction
from yakoon.base.transports import Transport
from yakoon.base.ui.event import ViewEvent
from yakoon.console.output import ConsoleOutput
from yakoon.console.ui import TerminalSurface, TerminalUI


class ConsoleClient:

    def __init__(self, transport: Transport):
        self.transport = transport

        # Form State
        self._current_fields = []
        self._current_index = 0
        self._current_values = {}

        # Document State (aus Patches gebaut)
        self._document_blocks = []
        self._document_header = None

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
            # Document aktualisieren
            # ------------------------
            if event.header:
                self._document_header = event.header

            self._apply_patch(event.patch)

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
    # Document Handling
    # --------------------------------------------------------

    def _apply_patch(self, patch):
        for op in patch.ops:

            if op.op == "reset":
                self._document_blocks = []

            elif op.op == "append_structure":
                for node in op.nodes:
                    block = node.props.get("block")
                    self._document_blocks.append(block)

            # später: replace/remove etc.

    # --------------------------------------------------------
    # View Ready
    # --------------------------------------------------------

    def _handle_view_ready(self, ui):

        header = self._document_header

        if not header or not header.expects_input:
            self._reset_form()
            ui.reset_prompt()
            return

        # FieldDefs extrahieren
        self._current_fields = self._extract_fields()
        self._current_index = 0
        self._current_values = {}

        self._show_next_prompt(ui)

    # --------------------------------------------------------
    # Fields
    # --------------------------------------------------------

    def _extract_fields(self):
        fields = []

        for block in self._document_blocks:
            for field in getattr(block, "fields", []):
                fields.append(field)

        return fields

    # --------------------------------------------------------
    # Prompt
    # --------------------------------------------------------

    def _show_next_prompt(self, ui):

        if self._current_index >= len(self._current_fields):
            return

        field = self._current_fields[self._current_index]

        ui.set_prompt(field)  # FieldDef direkt übergeben

    # --------------------------------------------------------
    # Helpers
    # --------------------------------------------------------

    def _reset_form(self):
        self._current_fields = []
        self._current_index = 0
        self._current_values = {}
