from __future__ import annotations

from yakoon.base.controllers import Controller, ResourceReferences

from .commands.patterns.cmdset import DemoCommandsPatterns


class DemoControllerPatterns(Controller):
    """Playground controller.

    This controller provides the default interactive environment.
    """

    id: str = "demo.patterns"

    commandsets = (DemoCommandsPatterns,)

    resources = ResourceReferences(
        package="yakoon.playground",
    )
