from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING

from yakoon.base.presentation import View, ViewHeader

if TYPE_CHECKING:
    from yakoon.base.capabilities.presenters import BlockGroup


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
