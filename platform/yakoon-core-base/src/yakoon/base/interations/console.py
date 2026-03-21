from yakoon.base.host import Interaction
from yakoon.base.ui import View


class ConsoleInteraction(Interaction):

    def __init__(self, ui):
        self.ui = ui

    async def show_prompt(self, ps1: str) -> None:
        self.ui.set_prompt(ps1)

    async def show_view(self, view: View) -> None:
        self.ui.render_view(view)

    async def exit(self) -> None:
        await self.ui.stop()
