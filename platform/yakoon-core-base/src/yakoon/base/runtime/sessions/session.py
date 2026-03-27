from typing import Protocol

from yakoon.base.capabilities.identity import PermissionSet
from yakoon.base.values import Key


class Session(Protocol):

    @property
    def lang(self) -> str: ...

    @property
    def key(self) -> Key: ...

    @property
    def permissions(self) -> PermissionSet: ...
