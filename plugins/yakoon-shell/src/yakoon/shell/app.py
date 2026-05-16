from yakoon.base.application import Application
from yakoon.base.plugins.ports import OnManualRegister, OnProjectionRegister
from yakoon.base.resources.resource import ResourceRef

from .controllers import SystemComposer, TestComposer


class ShellApp(Application):

    id: str = "shell"
    name = "shell"

    is_shell: bool = True

    composers = (
        SystemComposer,
        TestComposer,
    )

    def on_projection_register(self, on_register: OnProjectionRegister) -> None:

        projections = {
            "ls:overview": "ls/overview",
            "use:active": "use/active",
            "use:error": "use/error",
            "use:using": "use/using",
            "version:list": "version/list",
            "welcome:result": "welcome/result",
            "quit:confirm": "quit/confirm",
            "man:error": "man/error",
            "manual:ls": "ls/manual",
        }

        def register_projections(lang: str = "de"):
            for key, path in projections.items():
                on_register(
                    key=key,
                    scope="shell",
                    resource=ResourceRef(
                        package="yakoon.shell",
                        path=f"resources/{lang}/templates/{path}",
                    ),
                    lang=lang,
                )

        register_projections(lang="de")

    def on_manual_register(self, on_register: OnManualRegister) -> None:

        on_register(
            command="ls",
            scope="shell",
            projection="manual:ls",
        )
