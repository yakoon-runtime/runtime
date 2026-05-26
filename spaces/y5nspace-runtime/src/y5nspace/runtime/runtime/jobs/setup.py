from __future__ import annotations

from y5n.api.nodes import NodeSpace
from y5n.base.nodes.request import Request
from y5n.runtime.flow import Flow

from .ports import OnFlowGetByIndex, OnJobsList


async def setup(space: NodeSpace):

    def _enumerate_flows() -> list[tuple[int, Flow]]:
        session = space.session
        flows = [f for f in session.flows() if f.node.key != space.path.last]  # type: ignore
        return list(enumerate(flows, start=1))

    def _get_flow_by_index(request: Request) -> tuple[Flow | None, int | None]:
        try:
            index = int(request.arg(0))
        except (TypeError, ValueError):
            return None, None

        indexed = _enumerate_flows()

        for i, flow in indexed:
            if i == index:
                return flow, index

        return None, index

    space.ports.provide(OnJobsList, _enumerate_flows)
    space.ports.provide(OnFlowGetByIndex, _get_flow_by_index)
