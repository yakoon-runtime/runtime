from dataclasses import replace

from yakoon.base.capabilities.presenters import BlockGroup
from yakoon.base.ui import View, ViewHeader

from .steps import Ask, Show

# -----------------------------
# COMPILE
# -----------------------------


async def compile_view(
    view_id, view_header: ViewHeader | None, *, groups: list[BlockGroup], policy_service
):

    for group in groups:

        header = replace(
            view_header or ViewHeader(),
            expects_input=(group.type == "fields"),
        )

        subview = View(
            "view",
            header=header,
            id=view_id,
            blocks=group.blocks,
        )

        if group.type == "fields":
            yield Ask(subview, policy_service)
        else:
            yield Show(subview)
