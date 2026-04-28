from yakoon.base.application import Application

from .controller import ShellSystemController


class ShellApplication(Application):

    id: str = "shell-app"
    is_shell: bool = True

    controllers = (ShellSystemController,)
