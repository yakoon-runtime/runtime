from __future__ import annotations

from yakoon.base.controllers import Composer, ResourceReferences

from .commands.dsl.cmdset import DemoCommandsDsl


class DemoDslComposer(Composer):

    command_groups = (DemoCommandsDsl,)

    resources = ResourceReferences(
        package="yakoon.playground",
    )
