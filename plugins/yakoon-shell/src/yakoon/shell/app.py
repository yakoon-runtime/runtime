from yakoon.base.application import Application

from .controller import ShellCoreController


class ShellApplication(Application):

    id: str = "shell-app"
    is_shell: bool = True

    controllers = (ShellCoreController,)

    def create_command(self, controller, command, lang):
        command = super().create_command(controller, command, lang)

        if controller is ShellCoreController:
            pass

        return command
