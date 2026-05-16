from __future__ import annotations

from yakoon.base.controllers import Composer, ResourceReferences

from .commands.patterns.cmdset import DemoCommandsPatterns


class DemoPatternsComposer(Composer):

    command_groups = (DemoCommandsPatterns,)

    resources = ResourceReferences(
        package="yakoon.playground",
    )
