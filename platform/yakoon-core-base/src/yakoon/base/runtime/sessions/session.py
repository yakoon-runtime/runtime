from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from yakoon.base.capabilities.identity import PermissionSet
from yakoon.base.ui import ViewSpec
from yakoon.base.ui.stream.stream import OutputStreamPolicy
from yakoon.base.values import Key

if TYPE_CHECKING:
    from yakoon.base.ports import IO


_OUTPUT_STREAM_POLICY_KEY = "output_stream_policy"


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
    signals: set[str] = field(default_factory=set)
    io: IO | None = None
    meta: dict[str, Any] = field(default_factory=dict)


class Session:
    """
    Session output contract is strict:
      - emit/notify/fail accept ONLY ViewSpec mappings (kind='view')
      - mime is always application/yakoon.view+json
    """

    def __init__(self, state: SessionState):
        self._state = state
        self._runtime = SessionRuntime()

    @property
    def lang(self) -> str:
        return self._state.lang

    @property
    def key(self) -> Key:
        return self._state.key

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

    def touch(self) -> None:
        self._state.last_active = datetime.now(UTC)

    def bind_io(self, io: IO):
        self._runtime.io = io

    def set_username(self, username: str | None):
        self._state.username = username

    def get_username(self) -> str | None:
        return self._state.username

    def set_active_controller(self, controller_id: str) -> None:
        self._state.active_controller_id = controller_id

    def get_active_controller(self, default=None):
        return self._state.active_controller_id or default

    def set_identity(self, account_key, username: str) -> None:
        self._state.account_key = str(account_key)
        self._state.username = username

    def clear_identity(self) -> None:
        self._state.account_key = None
        self._state.username = None

    def has_identity(self) -> bool:
        return self._state.account_key is not None

    def signal(self, name: str) -> None:
        self._runtime.signals.add(name)

    def has_signal(self, name: str) -> bool:
        return name in self._runtime.signals

    def clear_signals(self) -> None:
        self._runtime.signals.clear()

    async def emit(self, payload: ViewSpec) -> None:
        view = self._ensure_view(payload)
        await self._runtime.io.view(view)

    # ----------------------------
    # Steaming output
    # ----------------------------

    def set_output_stream_policy(self, policy: OutputStreamPolicy) -> None:
        self._runtime.meta[_OUTPUT_STREAM_POLICY_KEY] = policy

    def get_output_stream_policy(self) -> OutputStreamPolicy:
        pol = self._runtime.meta.get(_OUTPUT_STREAM_POLICY_KEY)
        if isinstance(pol, OutputStreamPolicy):
            return pol
        return OutputStreamPolicy()

    # ----------------------------
    # Strict View output
    # ----------------------------

    def _ensure_view(self, payload: ViewSpec) -> ViewSpec:
        if not isinstance(payload, ViewSpec):
            raise TypeError("Session output must be a ViewSpec object.")
        if payload.kind != "view":
            raise TypeError("Session output must be a ViewSpec with kind='view'.")
        return payload
