from .ports import JOB_FLOW_GET, JOBS_LIST
from y5n.api.nodes import NodeSpace, Request


async def run(space: NodeSpace):

    def _enumerate_flows(session) -> list[tuple[int, object]]:
        flows = list(session.flows())
        flows = flows[:-1]
        return list(enumerate(flows, start=1))

    def _get_flow_by_index(session, request: Request) -> tuple[object | None, int | None]:
        try:
            index_str = request.option("stop") or request.option("fg") or request.arg(0)
            index = int(index_str)
        except (TypeError, ValueError):
            return None, None

        indexed = _enumerate_flows(session)

        for i, flow in indexed:
            if i == index:
                return flow, index

        return None, index

    space.ports.provide(JOBS_LIST, _enumerate_flows)
    space.ports.provide(JOB_FLOW_GET, _get_flow_by_index)
