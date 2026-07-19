"""Adapter: flow listing port for SDK commands."""

from __future__ import annotations

from typing import Any

from y5n.base.naming import Key
from y5n.base.runtime.context import Call


class FlowsAdapter:
    """Exposes session flow information to SDK commands."""

    def __init__(self, host: Any) -> None:
        self._host = host

    def get(
        self, call: Call, *, session_key: str = "", exclude_id: str = "", **kwargs: Any
    ) -> list[dict]:

        if not session_key:
            return []

        key = Key.from_str(session_key)
        runner = self._host._sessions.get(key)
        if not runner:
            return []

        result: list[dict] = []

        for idx, flow in enumerate(runner.session.flows(), start=1):
            if exclude_id and flow.id == exclude_id:
                continue

            result.append(
                {
                    "index": idx,
                    "id": flow.id,
                    "label": flow.node.name or flow.node.key,
                    "state": flow.control.label() if flow.control else "run",
                }
            )

        return result
