from __future__ import annotations

from collections.abc import Sequence
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any

from yakoon.base.capabilities.identity import PermissionSet
from yakoon.base.runtime.input import InputEvent
from yakoon.base.transports import IO
from yakoon.base.ui import (
    ViewEvent,
)
from yakoon.base.values import Key
from yakoon.platform.flow import Flow
from yakoon.platform.runtime.trace import ExecutionTrace


@dataclass
class SessionState:
    key: Key
    active_controller_id: str | None = None
    account_key: str | None = None
    username: str | None = None
    last_active: datetime | None = None
    lang: str = "de"
    data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        d = asdict(self)
        if self.last_active:
            d["last_active"] = self.last_active.astimezone(UTC).isoformat()
        else:
            d["last_active"] = None
        if self.key:
            d["key"] = str(self.key)
        return d

    @classmethod
    def from_dict(cls, d: dict) -> SessionState:
        if not d or "key" not in d:
            raise ValueError("SessionState requires a 'key'")

        d = dict(d)
        raw_key = d.pop("key")
        raw_last_active = d.pop("last_active", None)
        state = cls(key=Key.from_str(raw_key), **d)
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
      - mime is always application/yakoon.view+json
    """

    def __init__(self, state: SessionState):
        self._state = state
        self._runtime = SessionRuntime()
        self._flows: dict[str, Flow] = {}
        self._focus_flow_id: str | None = None
        self._runtime_flow_id: str | None = None

    # ========================================================
    # PUBLIC API
    # ========================================================

    @property
    def lang(self) -> str:
        return self._state.lang

    @property
    def key(self) -> Key:
        return self._state.key

    @property
    def execution(self) -> ExecutionTrace:
        return self._runtime.execution

    @property
    def state(self) -> SessionState:
        return self._state

    @property
    def permissions(self) -> PermissionSet:
        return self._runtime.permissions

    def set_permissions(self, permset: PermissionSet) -> None:
        self._runtime.permissions = permset

    @classmethod
    def from_state(cls, state: SessionState) -> Session:
        return cls(state)

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
            self.set_focus(None)

    def set_focus(self, flow_id: str | None):
        if flow_id and flow_id not in self._flows:
            return
        self._focus_flow_id = flow_id

    def flows(self) -> Sequence[Flow]:
        return list(self._flows.values())

    @property
    def focused_flow(self) -> Flow | None:
        if not self._focus_flow_id:
            return None
        return self.get_flow(self._focus_flow_id)

    # ----------------------------
    # event
    # ----------------------------

    def send_event(self, event: InputEvent) -> bool:
        flow = self.focused_flow
        if not flow:
            return False

        flow.push_event(event)
        return True

    # ----------------------------
    # TOUCH
    # ----------------------------

    def touch(self) -> None:
        self._state.last_active = datetime.now(UTC)

    # ----------------------------
    # Username
    # ----------------------------

    def set_username(self, username: str | None):
        self._state.username = username

    def get_username(self) -> str | None:
        return self._state.username

    # ----------------------------
    # Contoller
    # ----------------------------

    def set_active_controller(self, controller_id: str) -> None:
        self._state.active_controller_id = controller_id

    def get_active_controller(self, default=None) -> str | None:
        return self._state.active_controller_id or default

    # ----------------------------
    # Identity
    # ----------------------------

    def set_identity(self, account_key, username: str) -> None:
        self._state.account_key = str(account_key)
        self._state.username = username

    def clear_identity(self) -> None:
        self._state.account_key = None
        self._state.username = None

    def has_identity(self) -> bool:
        return self._state.account_key is not None

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
        event: ViewEvent,
        *,
        job_id: str | None = None,
        channel: str = "main",
    ) -> None:
        job_id = job_id or self._runtime_flow_id or "system"
        if type(event) is not ViewEvent:
            raise RuntimeError(f"Expected ViewEvent, got {type(event).__name__}")

        if self._runtime.io is None:
            raise RuntimeError("io cannot be None")
        await self._runtime.io.view(event)
