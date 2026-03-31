from yakoon.base.dispatch import Interaction
from yakoon.base.projection import Projection


class ConsoleInteraction(Interaction):

    def __init__(self, ui):
        self.ui = ui

    async def show_prompt(self, ps1: str) -> None:
        self.ui.set_prompt(ps1)

    async def show_projection(self, projection: Projection) -> None:
        self.ui.render_projection(projection)

    async def exit(self) -> None:
        await self.ui.stop()
