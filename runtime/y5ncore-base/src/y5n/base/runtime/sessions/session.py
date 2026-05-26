from typing import Protocol

from y5n.base.naming import Key
from y5n.runtime.capabilities.permission import PermissionSet


class Session(Protocol):

    @property
    def lang(self) -> str: ...

    @property
    def key(self) -> Key: ...

    @property
    def permissions(self) -> PermissionSet: ...
    def set_permissions(self, permset: PermissionSet) -> None: ...

    def set_identity(self, user_key) -> None: ...
    def get_identity(self) -> Key | None: ...
