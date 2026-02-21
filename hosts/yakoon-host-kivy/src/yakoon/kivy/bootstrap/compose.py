from __future__ import annotations

from dataclasses import dataclass

from yakoon.auth.controller import AuthCoreController
from yakoon.compose.engine import compose_engine
from yakoon.kivy.bootstrap.dispatcher import ContextDispatcher
from yakoon.kivy.controllers.app_controller import AppController
from yakoon.kivy.pages.app_root_page import AppRootPage
from yakoon.kivy.runtime.runner import SessionRunner
from yakoon.platform.directories.controller import ControllerDirectory
from yakoon.shell.controller import ShellCoreController


@dataclass
class KivyComposition:
    root: AppRootPage
    controller: AppController
    runner: SessionRunner
    dispatcher: ContextDispatcher
    engine: object


def compose_kivy_app() -> KivyComposition:

    engine = compose_engine(
        controllers=ControllerDirectory(
            controllers=[ShellCoreController(), AuthCoreController()]
        )
    )

    runner = SessionRunner(engine)
    runner.start()

    root = AppRootPage()
    dispatcher = ContextDispatcher()

    controller = AppController(root, dispatcher, runner)
    dispatcher.set_handler(controller.dispatch_context)

    controller.new_chat_tab(select=True)

    return KivyComposition(
        root=root,
        controller=controller,
        runner=runner,
        dispatcher=dispatcher,
        engine=engine,
    )
