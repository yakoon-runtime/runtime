from dataclasses import replace

from yakoon.base.capabilities.presenters.types import BlockGroup
from yakoon.base.ui.document import ViewHeader, ViewSpec

from .steps.step import Ask, Show

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

        subview = ViewSpec(
            "view",
            header=header,
            id=view_id,
            blocks=group.blocks,
        )

        if group.type == "fields":
            # ! result is
            result = yield Ask(subview, policy_service)
        else:
            yield Show(subview)
