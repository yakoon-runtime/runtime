from __future__ import annotations

from y5n.base.controllers import Composer, ResourceReferences

from .commands.patterns.cmdset import DemoCommandsPatterns


class DemoPatternsComposer(Composer):

    command_groups = (DemoCommandsPatterns,)

    resources = ResourceReferences(
        package="y5n.playground",
    )
