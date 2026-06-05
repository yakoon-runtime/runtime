from __future__ import annotations

from y5n.api.flow import Flow
from y5n.api.nodes import NodeSpace, Request

from .ports import OnFlowGetByIndex, OnJobsList


async def setup(space: NodeSpace):

    def _enumerate_flows(session) -> list[tuple[int, Flow]]:
        flows = list(session.flows())

        # Exclude current jobs flow
        flows = flows[:-1]

        return list(enumerate(flows, start=1))

    def _get_flow_by_index(session, request: Request) -> tuple[Flow | None, int | None]:
        try:
            index = int(request.arg(0))
        except (TypeError, ValueError):
            return None, None

        indexed = _enumerate_flows(session)

        for i, flow in indexed:
            if i == index:
                return flow, index

        return None, index

    space.ports.provide(OnJobsList, _enumerate_flows)
    space.ports.provide(OnFlowGetByIndex, _get_flow_by_index)
