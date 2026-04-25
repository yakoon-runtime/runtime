from __future__ import annotations

from yakoon.base.controllers import Controller, ResourceReferences

from .commands.dsl.cmdset import DemoCommandsDsl


class DemoControllerDsl(Controller):
    """Playground controller.

    This controller provides the default interactive environment.
    """

    id: str = "demo.dsl"

    commandsets = (DemoCommandsDsl,)

    resources = ResourceReferences(
        package="yakoon.playground",
    )
