from typing import Protocol

from yakoon.base.capabilities.interaction import FieldPolicyEngine


class DslContext(Protocol):

    @property
    def policies(self) -> FieldPolicyEngine: ...
