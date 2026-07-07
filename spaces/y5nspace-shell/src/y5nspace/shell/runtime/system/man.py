from y5n.api.data import DataRequest
from y5n.api.dsl import out
from y5n.api.nodes import NodeSpace
from y5n.api.ports import OnManualResolve, OnSourceRead
from y5n.api.projections import Projection

from ...ports import OnProject


async def run(space: NodeSpace):

    key = space.request.arg(0)

    current_node = space.session.get_current_node()  # type: ignore

    # ----------------------------------
    # Resolve visible nodes
    # ----------------------------------

    found = None
    on_source = space.ports.get(OnSourceRead)

    if "/" in key:
        parent_name, child_name = key.rsplit("/", 1)
        parent_result = await on_source(
            DataRequest(f"system:nodes --by-key {parent_name}")
        )

        parent_path = ""
        scope_result = await on_source(
            DataRequest(f"system:nodes --scope {current_node}")
        )
        parent = next((x for x in scope_result.rows if x["key"] == parent_name), None)

        if parent:
            parent_path = parent["path"]
        elif parent_result.status == "ok":
            parent_path = parent_result.one()["path"]

        if parent_path:
            child_result = await on_source(
                DataRequest(f"system:nodes --scope {parent_path}")
            )
            found = next((x for x in child_result.rows if x["key"] == child_name), None)

    else:
        result = await on_source(DataRequest(f"system:nodes --scope {current_node}"))
        found = next((x for x in result.rows if x["key"] == key), None)

    # ----------------------------------
    # Node not found
    # ----------------------------------

    if not found:
        projection = await space.ports.get(OnProject)(
            name="man/missing",
            lang=space.session.lang,
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
    ports = space.ports_from(path=found["path"], absolute=True)
    if ports and ports.has(OnManualResolve):
        on_manual_resolve = ports.get(OnManualResolve)
        try:
            projection = await on_manual_resolve(
                key=found["path"],
                lang=space.request.lang,
            )
        except LookupError:
            pass

    # ----------------------------------
    # Manual missing
    # ----------------------------------

    if not projection:
        projection = await space.ports.get(OnProject)(
            name="man/missing",
            lang=space.session.lang,
            state={
                "key": key,
            },
        )

        yield out(projection)
        return

    yield out(projection)
