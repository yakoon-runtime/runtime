from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING

from yakoon.base.projection import Projection, ProjectionHeader

if TYPE_CHECKING:
    from yakoon.base.capabilities.projection import BlockGroup


async def compile_view(
    projection_id,
    header: ProjectionHeader | None,
    *,
    groups: list[BlockGroup],
    policy_service,
):

    for group in groups:

        header = replace(
            header or ProjectionHeader(),
        )

        subview = Projection.create(
            header=header,
            blocks=group.blocks,
        )

        if group.type == "fields":
            yield Ask(subview, policy_service)
        else:
            yield Show(subview)
