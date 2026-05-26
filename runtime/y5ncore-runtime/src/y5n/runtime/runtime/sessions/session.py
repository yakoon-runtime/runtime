from __future__ import annotations

from collections.abc import Sequence
from dataclasses import asdict, dataclass, field, replace
from datetime import UTC, datetime
from typing import Any

from y5n.base.naming import Key
from y5n.base.nodes.path import NodePath
from y5n.base.projection import (
    ProjectionEvent,
    ProjectionState,
)
from y5n.base.transport import IO
from y5n.runtime.capabilities.permission import PermissionSet
from y5n.runtime.flow import Flow
from y5n.runtime.runtime.trace import ExecutionTrace
from y5nstore.event import GetResult


@dataclass
class SessionData:

    CURRENT_VERSION = 1

    node_path: str | None = None
    user_key: str | None = None
    account_key: str | None = None
    last_active: datetime | None = None
    lang: str = "de"
    debug: bool = True
    data: dict[str, Any] = field(default_factory=dict)
    _v: int = field(default=CURRENT_VERSION)

    def to_dict(self) -> dict:
        d = asdict(self)
        if self.last_active:
            d["last_active"] = self.last_active.astimezone(UTC).isoformat()
        return d

    @classmethod
    def from_dict(cls, d: dict) -> SessionData:

        d = dict(d)
        raw_last_active = d.pop("last_active", None)
        state = cls(**d)
        if raw_last_active:
            state.last_active = datetime.fromisoformat(raw_last_active)
        return state


@dataclass
class SessionRuntime:
    permissions: PermissionSet = field(default_factory=PermissionSet)
    marks: set[str] = field(default_factory=set)
    io: IO | None = None
    meta: dict[str, Any] = field(default_factory=dict)
    execution: ExecutionTrace = field(default_factory=ExecutionTrace)


class Session:
    """
    Session output contract is strict:
      - emit/notify/fail accept ONLY View mappings (kind='view')
      - mime is always application/y5n.view+json
    """

    def __init__(self, key: Key, data: SessionData):
        self.key = key
        self.data = data

        self._runtime = SessionRuntime()
        self._flows: dict[str, Flow] = {}
        self._focus_flow_id: str | None = None
        self._runtime_flow_id: str | None = None

    # ========================================================
    # PUBLIC API
    # ========================================================

    @property
    def lang(self) -> str:
        return self.data.lang

    @property
    def debug(self) -> bool:
        return self.data.debug

    @property
    def execution(self) -> ExecutionTrace:
        return self._runtime.execution

    @property
    def permissions(self) -> PermissionSet:
        return self._runtime.permissions

    def set_permissions(self, permset: PermissionSet) -> None:
        self._runtime.permissions = permset

    @classmethod
    def from_row(cls, row: GetResult) -> Session:
        data = row.require_object()
        return cls(
            key=row.key,
            data=SessionData.from_dict(data),
        )

    # ========================================================
    # SYSTEM API
    # ========================================================

    # ----------------------------
    # bind
    # ----------------------------

    def bind_io(self, io: IO):
        self._runtime.io = io

    # ----------------------------
    # flow
    # ----------------------------

    def add_flow(self, flow: Flow) -> str:
        self._flows[flow.id] = flow
        return flow.id

    def get_flow(self, id: str) -> Flow | None:
        return self._flows.get(id)

    def del_flow(self, flow: Flow):
        if flow.id in self._flows:
            del self._flows[flow.id]
        if flow.id == self._focus_flow_id:
            self.set_interaction(None)

    def flows(self) -> Sequence[Flow]:
        return list(self._flows.values())

    def has_interaction(self) -> bool:
        return bool(self.interaction_flow)

    def set_interaction(self, flow_id: str | None):
        if flow_id and flow_id not in self._flows:
            return
        self._focus_flow_id = flow_id

    @property
    def interaction_flow(self) -> Flow | None:
        if not self._focus_flow_id:
            return None
        return self.get_flow(self._focus_flow_id)

    # ----------------------------
    # TOUCH
    # ----------------------------

    def touch(self) -> None:
        self.data.last_active = datetime.now(UTC)

    # ----------------------------
    # NODE
    # ----------------------------

    def set_current_node(self, path: NodePath) -> None:
        self.data.node_path = str(path)

    def get_current_node(self, default=None) -> NodePath:
        return NodePath.from_string(self.data.node_path or default)

    # ----------------------------
    # Identity
    # ----------------------------

    def set_identity(self, user_key) -> None:
        self.data.user_key = str(user_key)

    def get_identity(self) -> Key | None:
        if self.data.user_key:
            return Key.from_str(self.data.user_key)
        return None

    def clear_identity(self) -> None:
        self.data.user_key = None

    def has_identity(self) -> bool:
        return self.data.user_key is not None

    # ----------------------------
    # Account
    # ----------------------------

    def set_active_account(self, account_key) -> None:
        self.data.account_key = str(account_key)

    def clear_active_account(self) -> None:
        self.data.account_key = None

    def has_active_account(self) -> bool:
        return self.data.account_key is not None

    # ----------------------------
    # Mark
    # ----------------------------

    def mark(self, name: str) -> None:
        self._runtime.marks.add(name)

    def has_mark(self, name: str) -> bool:
        return name in self._runtime.marks

    def clear_marks(self) -> None:
        self._runtime.marks.clear()

    # ----------------------------
    # emit
    # ----------------------------

    async def emit(
        self,
        event: ProjectionEvent,
    ) -> None:

        assert (
            type(event) is ProjectionEvent
        ), f"event must be a type of {type(event).__name__}"
        assert self._runtime.io is not None, "runtime.io must not be None"
        assert event.job_id, "event.job_id must be set"

        event = self._attach_state(event)
        await self._runtime.io.view(event)

    def _attach_state(self, event: ProjectionEvent) -> ProjectionEvent:
        return replace(
            event,
            state=ProjectionState(
                user="NO-USER!",
                # user=self.get_username(),
                # controller=self.get_current_node(),
            ),
        )
