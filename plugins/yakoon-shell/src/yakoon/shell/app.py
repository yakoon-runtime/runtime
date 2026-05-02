from yakoon.base.application import Application

from .controllers import SystemController, TestController


class ShellApp(Application):

    id: str = "shell-app"
    name = "shell"

    is_shell: bool = True

    controllers = (
        SystemController,
        TestController,
    )
