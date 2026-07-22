from collections.abc import Sequence

from y5n.runtime.engine.flow.primitives import (
    Background,
    Effect,
    EmitEvent,
    EmitView,
    Foreground,
    StartCommand,
    StartTask,
)
from y5n.runtime.flow import Flow
from y5n.runtime.runtime import Session

from .handlers import (
    BackgroundHandler,
    EmitEventHandler,
    EmitViewHandler,
    ForegroundHandler,
    StartCommandHandler,
    StartTaskHandler,
)
from .protocol import EffectHandler


class EffectExecutor:
    """Dispatches effects to their registered handlers.

    The executor maintains a registry mapping effect types to handler
    instances.  Callers (typically the engine via the OnApplyEffects
    port) pass a sequence of effects; the executor looks up each
    effect's handler and runs it.

    Handlers are registered at construction time.  Additional handlers
    can be added later via register() — this is primarily used by
    tests that need to intercept specific effect types.
    """

    _handlers: dict[type[Effect], EffectHandler]

    def __init__(self, on_projection, on_start_task, on_start_command):
        self._on_projection = on_projection
        self.on_start_task = on_start_task
        self.on_start_command = on_start_command

        self._handlers = {
            EmitView: EmitViewHandler(on_projection),
            Foreground: ForegroundHandler(),
            Background: BackgroundHandler(),
            EmitEvent: EmitEventHandler(),
            StartTask: StartTaskHandler(on_start_task),
            StartCommand: StartCommandHandler(on_start_command),
        }

    def register(self, effect_type: type[Effect], handler: EffectHandler) -> None:
        self._handlers[effect_type] = handler

    async def execute(
        self,
        effects: Sequence[Effect],
        session: Session,
        flow: Flow,
    ) -> None:
        for effect in effects:
            handler = self._handlers.get(type(effect))
            if handler is None:
                raise ValueError(f"No handler registered for {type(effect).__name__}")
            await handler.execute(effect, session, flow)
