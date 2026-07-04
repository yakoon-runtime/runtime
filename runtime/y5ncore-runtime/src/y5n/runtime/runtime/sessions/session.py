from __future__ import annotations

from collections import deque
from collections.abc import Sequence
from dataclasses import asdict, dataclass, field, replace
from datetime import UTC, datetime
from typing import Any

from y5n.base.clients import ClientConnection
from y5n.base.flow.channel import Scope, resolve
from y5n.base.naming import Key
from y5n.base.nodes.path import NodePath
from y5n.base.projection import (
    ProjectionEvent,
    ProjectionState,
)
from y5n.base.runtime import Event
from y5n.base.runtime.input import Interaction
from y5n.base.transport import IO
from y5n.runtime.capabilities.permission import PermissionSet
from y5n.runtime.flow import Flow
from y5n.runtime.runtime.bus import SessionBus
from y5nstore.event import GetResult


@dataclass
class SessionData:

    CURRENT_VERSION = 1

    node_path: str | None = None
    user_key: str | None = None
    user_name: str | None = None
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

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self.data[key] = value

    def pop(self, key: str, default: Any = None) -> Any:
        return self.data.pop(key, default)

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
    interaction: Interaction = Interaction.CLI


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
        self._bus = SessionBus()
        self._flow_id_counter = 0
        self._flows: dict[str, Flow] = {}
        self._foreground_flow_id: str | None = None
        self._channels: dict[str, deque[Event]] = {}  # resolved channel key → queue

    # ========================================================
    # PUBLIC API
    # ========================================================

    @property
    def lang(self) -> str:
        return self.data.lang

    @property
    def interaction(self) -> Interaction:
        return self._runtime.interaction

    @interaction.setter
    def interaction(self, value: Interaction) -> None:
        self._runtime.interaction = value

    @property
    def debug(self) -> bool:
        return self.data.debug

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
    # client lifecycle
    # ----------------------------

    def join(self, client: ClientConnection):
        self._bus.join(client)

    def leave(self, client: ClientConnection):
        self._bus.leave(client)

    # ----------------------------
    # flow
    # ----------------------------

    def add_flow(self, flow: Flow) -> str:
        self._flows[flow.id] = flow
        return flow.id

    def next_flow_id(self) -> str:
        n = self._flow_id_counter
        self._flow_id_counter += 1
        return str(n)

    def get_flow(self, id: str) -> Flow | None:
        return self._flows.get(id)

    def del_flow(self, flow: Flow):
        if flow.id in self._flows:
            del self._flows[flow.id]
        prefix = f"{flow.id}:"
        self._channels = {
            k: v for k, v in self._channels.items() if not k.startswith(prefix)
        }
        if flow.id == self._foreground_flow_id:
            self.set_foreground_flow(None)

    def flows(self) -> Sequence[Flow]:
        return list(self._flows.values())

    def has_foreground_flow(self) -> bool:
        return bool(self.foreground_flow)

    def set_foreground_flow(self, flow_id: str | None):
        if flow_id and flow_id not in self._flows:
            return
        self._foreground_flow_id = flow_id

    @property
    def foreground_flow(self) -> Flow | None:
        if not self._foreground_flow_id:
            return None
        return self.get_flow(self._foreground_flow_id)

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

    def set_identity(self, user_key, user_name: str | None = None) -> None:
        self.data.user_key = str(user_key)
        self.data.user_name = user_name

    def get_identity(self) -> Key | None:
        if self.data.user_key:
            return Key.from_str(self.data.user_key)
        return None

    def get_identity_name(self) -> str | None:
        return self.data.user_name

    def clear_identity(self) -> None:
        self.data.user_key = None
        self.data.user_name = None

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
                user=self.data.user_name,
                node_path=self.data.node_path,
            ),
        )

    # ========================================================
    # CHANNELS
    # ========================================================

    def push_event(
        self,
        scope: Scope,
        channel: str,
        event: Event,
        *,
        flow: Flow | None = None,
    ) -> None:
        key = resolve(scope, channel, flow=flow)
        if key not in self._channels:
            self._channels[key] = deque()
        self._channels[key].append(event)

    def pop_event(
        self,
        scope: Scope,
        channel: str,
        *,
        flow: Flow | None = None,
    ) -> Event | None:
        key = resolve(scope, channel, flow=flow)
        q = self._channels.get(key)
        if q:
            return q.popleft()
        return None

    def has_mail(
        self,
        scope: Scope,
        channel: str,
        *,
        flow: Flow | None = None,
    ) -> bool:
        key = resolve(scope, channel, flow=flow)
        q = self._channels.get(key)
        return bool(q)
