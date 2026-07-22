from __future__ import annotations

from collections import deque
from collections.abc import Sequence
from dataclasses import asdict, dataclass, field, replace
from datetime import UTC, datetime
from typing import Any

from y5n.runtime.engine.clients import ClientConnection
from y5n.runtime.engine.document import (
    DocumentEvent,
    DocumentState,
)
from y5n.runtime.engine.flow.channel import Scope, resolve
from y5n.runtime.engine.naming import Key
from y5n.runtime.engine.runtime import Event
from y5n.runtime.engine.runtime.input import Interaction
from y5n.runtime.engine.transport import IO
from y5n.runtime.capabilities.permission import PermissionSet
from y5n.runtime.flow import Flow
from y5n.runtime.runtime.bus import SessionBus
from y5nstore.event import GetResult


@dataclass
class SessionData:

    CURRENT_VERSION = 1

    current_path: str | None = None
    user_key: str | None = None
    user_name: str | None = None
    last_active: datetime | None = None
    lang: str = "en"
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


class Session:
    """
    Session output contract is strict:
      - emit/notify/fail accept ONLY View mappings (kind='view')
      - mime is always application/y5n.view+json
    """

    def __init__(self, key: Key, data: SessionData):

        self.key = key
        self.data = data
        self.interaction: Interaction = Interaction.CLI

        self._permissions: PermissionSet = PermissionSet()
        self._io: IO | None = None
        self._bus = SessionBus()
        self._flow_id_counter = 0
        self._flows: dict[str, Flow] = {}
        self._foreground_flow_id: str | None = None
        self._channels: dict[str, deque[Event]] = {}

    # ========================================================
    # PUBLIC API
    # ========================================================

    @property
    def lang(self) -> str:
        return self.data.lang

    def get_data(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)

    def set_data(self, key: str, value: Any) -> None:
        self.data.set(key, value)

    def del_data(self, key: str, default: Any = None) -> Any:
        return self.data.pop(key, default)

    @property
    def permissions(self) -> PermissionSet:
        return self._permissions

    def set_permissions(self, permset: PermissionSet) -> None:
        self._permissions = permset

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
        self._io = io

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

    def flows(self, exclude: str | None = None) -> Sequence[Flow]:
        if exclude is None:
            return list(self._flows.values())
        return [f for f in self._flows.values() if f.id != exclude]

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
    # CURRENT PATH
    # ----------------------------

    def set_cwd(self, path: str) -> None:
        self.data.current_path = path

    @property
    def cwd(self) -> str:
        return self.data.current_path or ""

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

    @property
    def user_name(self) -> str | None:
        return self.data.user_name

    # ----------------------------
    # emit
    # ----------------------------

    async def emit(
        self,
        event: DocumentEvent,
    ) -> None:

        assert (
            type(event) is DocumentEvent
        ), f"event must be a type of {type(event).__name__}"
        assert self._io is not None, "runtime.io must not be None"
        assert event.job_id, "event.job_id must be set"

        event = self._attach_state(event)
        await self._io.view(event)

    def _attach_state(self, event: DocumentEvent) -> DocumentEvent:
        return replace(
            event,
            state=DocumentState(
                user=self.data.user_name,
                node_path=self.data.current_path,
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
