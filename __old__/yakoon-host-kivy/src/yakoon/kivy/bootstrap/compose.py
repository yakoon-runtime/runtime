from __future__ import annotations

from dataclasses import dataclass

from yakoon.kivy.bootstrap.dispatcher import ContextDispatcher
from yakoon.kivy.controllers.app_controller import AppController
from yakoon.kivy.pages.app_root_page import AppRootPage
from yakoon.kivy.runner import SessionRunner
from yakoon.platform.wire.runtime import build_runtime


@dataclass
class KivyComposition:
    root: AppRootPage
    controller: AppController
    runner: SessionRunner
    dispatcher: ContextDispatcher
    engine: object


def compose_kivy_app() -> KivyComposition:

    engine = build_runtime(
        plugins=[
            "yakoon.shell",
        ],
        capabilities={
            "audit": "default",
            "discovery": "default",
            "identity": "default",
            "interaction": "default",
            "projectors": "default",
            "workflow": "default",
        },
    )

    runner = SessionRunner(engine)
    runner.start()

    root = AppRootPage()
    dispatcher = ContextDispatcher()

    controller = AppController(root, dispatcher, runner)
    dispatcher.set_handler(controller.dispatch_context)

    # Startet den ersten Tab (erstellt Session+Output im TabsController)
    controller.new_chat_tab(select=True)

    return KivyComposition(
        root=root,
        controller=controller,
        runner=runner,
        dispatcher=dispatcher,
        engine=engine,
    )
