import asyncio

from yakoon.base.host import InputEvent, TextInput
from yakoon.base.interations import DefaultInteraction
from yakoon.base.transports import Transport
from yakoon.console.output import ConsoleOutput
from yakoon.console.ui import TerminalSurface, TerminalUI


class ConsoleClient:

    def __init__(self, transport: Transport):
        self.transport = transport

    async def run(self):

        async def cancel() -> None:
            await connection.send_input(TextInput("__cancel__"))

        async def submit(event: InputEvent) -> None:
            await connection.send_input(event)

        surface = TerminalSurface()
        renderer = ConsoleOutput(surface)
        ui = TerminalUI(surface, on_cancel=cancel)
        interaction = DefaultInteraction(ui.read_line, submit)

        async def on_emit(event):
            await renderer.view(event)

        connection = await self.transport.connect(
            on_emit=on_emit,
            io=renderer,
            interaction=interaction,
        )

        async with asyncio.TaskGroup() as tg:
            tg.create_task(renderer.run())
            tg.create_task(ui.run())

        await interaction.exit()
