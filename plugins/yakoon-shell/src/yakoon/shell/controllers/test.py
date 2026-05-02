from __future__ import annotations

from yakoon.base.commands import Command
from yakoon.base.controllers import Controller, ResourceReferences

from ..commands.test import (
    CmdTest,
    CmdTestCity,
    TestCommands,
)


class TestController(Controller):

    id: str = "shell-test-controller"

    commandsets = (TestCommands,)

    resources = ResourceReferences(
        package="yakoon.shell",
    )

    command_builders: dict[type[Command], str] = {
        CmdTest: "_create_test",
        CmdTestCity: "_create_test_city",
    }

    # ----------------------------------
    # CREATE COMMAND
    # ----------------------------------

    def create_command(
        self,
    ) -> Command:
        name = self.command_builders.get(self.command)
        if name:
            return getattr(self, name)()

        raise RuntimeError("invalid command")

    # ----------------------------------
    # FACTORY
    # ----------------------------------
    def _create_test(self):
        return CmdTest()

    def _create_test_city(self):
        return CmdTestCity(on_project=self.project)
