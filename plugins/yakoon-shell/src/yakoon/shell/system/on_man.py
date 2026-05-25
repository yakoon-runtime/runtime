from yakoon.base.flow import out
from yakoon.base.nodes import RuntimeContext
from yakoon.base.plugins.ports import OnManualResolve
from yakoon.base.projection import Projection
from yakoon.base.sources import (
    DataRequest,
    OnSourceRead,
)

from ..ports import OnProject


async def on_man(ctx: RuntimeContext):

    key = ctx.request.arg(0)

    current_node = ctx.session.get_current_node()

    # ----------------------------------
    # Resolve visible nodes
    # ----------------------------------

    on_source = ctx.ports.get(OnSourceRead)

    result = await on_source(DataRequest(f"system:nodes --scope {current_node}"))
    found = next((x for x in result.rows if x["key"] == key), None)

    # ----------------------------------
    # Node not found
    # ----------------------------------

    if not found:
        projection = await ctx.ports.get(OnProject)(
            name="man/missing",
            lang=ctx.session.lang,
            state={
                "key": key,
            },
        )

        yield out(projection)
        return

    # ----------------------------------
    # Resolve manual
    # ----------------------------------

    projection: Projection | None = None
    ports = ctx.ports_from(path=found["path"], absolute=True)
    if ports and ports.has(OnManualResolve):
        on_manual_resolve = ports.get(OnManualResolve)
        try:
            projection = await on_manual_resolve(
                key=found["path"],
                lang=ctx.request.lang,
            )
        except Exception:
            pass

    # ----------------------------------
    # Manual missing
    # ----------------------------------

    if not projection:
        projection = await ctx.ports.get(OnProject)(
            name="man/missing",
            lang=ctx.session.lang,
            state={
                "key": key,
            },
        )

        yield out(projection)
        return

    yield out(projection)
