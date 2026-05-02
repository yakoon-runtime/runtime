from yakoon.base.application import Application

from .controllers import SystemController, TestController


class ShellApplication(Application):

    id: str = "shell-app"
    is_shell: bool = True

    controllers = (
        SystemController,
        TestController,
    )
