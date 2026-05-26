from typing import Protocol

from y5n.base.capabilities.interaction import FieldPolicyEngine


class DslContext(Protocol):

    @property
    def policies(self) -> FieldPolicyEngine: ...
