from collections.abc import Sequence
from typing import Protocol

from yakoon.base.capabilities.identity import PermissionSet
from yakoon.base.runtime.flow import Flow
from yakoon.base.runtime.input import InputEvent
from yakoon.base.transports import IO
from yakoon.base.ui import View, ViewEvent
from yakoon.base.values import Key


class CommandSession(Protocol):

    @property
    def lang(self) -> str: ...

    @property
    def key(self) -> Key: ...

    @property
    def permissions(self) -> PermissionSet: ...

    async def emit(
        self,
        payload: View | ViewEvent,
        *,
        job_id: str | None = None,
        channel: str = "main",
    ) -> None: ...


class Session(CommandSession):

    # ========================================================
    # PUBLIC (State)
    # ========================================================

    def set_permissions(self, permset: PermissionSet) -> None: ...

    # ========================================================
    # Flow Management
    # ========================================================

    def add_flow(self, flow: Flow) -> str: ...

    def get_flow(self, id: str) -> Flow | None: ...

    def del_flow(self, flow: Flow) -> None: ...

    def set_focus(self, flow_id: str | None) -> None: ...

    def flows(self) -> Sequence[Flow]: ...

    @property
    def focused_flow(self) -> Flow | None: ...

    # ========================================================
    # Input Routing
    # ========================================================

    def send_event(self, event: InputEvent) -> bool: ...

    # ========================================================
    # Lifecycle
    # ========================================================

    def touch(self) -> None: ...

    # ========================================================
    # Identity / User
    # ========================================================

    def set_username(self, username: str | None) -> None: ...

    def get_username(self) -> str | None: ...

    def set_identity(self, account_key, username: str) -> None: ...

    def clear_identity(self) -> None: ...

    def has_identity(self) -> bool: ...

    # ========================================================
    # Controller
    # ========================================================

    def set_active_controller(self, controller_id: str) -> None: ...

    def get_active_controller(self, default=None) -> str | None: ...

    # ========================================================
    # Marks (Runtime Flags)
    # ========================================================

    def mark(self, name: str) -> None: ...

    def has_mark(self, name: str) -> bool: ...

    def clear_marks(self) -> None: ...

    # ========================================================
    # IO Binding (Infra)
    # ========================================================

    def bind_io(self, io: IO) -> None: ...
