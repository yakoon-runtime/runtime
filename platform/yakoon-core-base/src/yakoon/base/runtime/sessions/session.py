from typing import Protocol

from yakoon.base.naming import Key
from yakoon.platform.capabilities.permission import PermissionSet


class Session(Protocol):

    @property
    def lang(self) -> str: ...

    @property
    def key(self) -> Key: ...

    @property
    def permissions(self) -> PermissionSet: ...

    def set_identity(self, user_key) -> None: ...
    def get_identity(self) -> Key | None: ...
