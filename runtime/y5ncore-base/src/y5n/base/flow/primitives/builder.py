from collections.abc import Sequence

from y5n.base.projection.model import (
    Block,
    ErrorKind,
    Projection,
    ProjectionHeader,
    Role,
)


def create_projection(
    *,
    blocks: Sequence[Block],
    role: Role = "info",
    title: str | None = None,
    error_kind: ErrorKind | None = None,
    error_code: str | None = None,
) -> Projection:

    header = ProjectionHeader(
        role=role,
        title=title,
        error_kind=error_kind,
        error_code=error_code,
        meta=None,
    )

    return Projection.create(
        header=header,
        blocks=list(blocks),
    )
