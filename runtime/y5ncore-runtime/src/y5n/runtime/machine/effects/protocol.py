from typing import Protocol

from y5n.runtime.engine.flow.primitives import Effect
from y5n.runtime.flow import Flow
from y5n.runtime.runtime import Session


class EffectHandler(Protocol):
    """Protocol for effect handler implementations.

    Each effect type has a dedicated handler that knows how to apply
    the effect's semantic side effect to the runtime.
    """

    async def execute(self, effect: Effect, session: Session, flow: Flow) -> None: ...
