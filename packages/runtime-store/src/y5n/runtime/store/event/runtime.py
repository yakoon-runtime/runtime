from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from .store import EntityStore

if TYPE_CHECKING:
    from y5n.runtime.store.sequence.runtime import Sequencer


class StoreRuntime:
    """The complete runtime contract of one physical store.

    A ``StoreFactory`` materializes the full store: the entity objects
    *and* its sequencer. Sequencing is part of the storage semantics —
    the runtime never marries a store to a sequencer itself.
    """

    def __init__(
        self,
        objects: EntityStore,
        sequencer: Sequencer | None = None,
        on_initialize: Oninitialize | None = None,
        on_shutdown: OnShutdown | None = None,
    ):
        self.objects = objects
        self.sequencer = sequencer
        self.on_initialize = on_initialize
        self.on_shutdown = on_shutdown

    # -----------------
    # --- LIFECYCLE ---
    # -----------------

    async def initialize(self):
        if self.on_initialize:
            await self.on_initialize()
        if self.sequencer is not None:
            await self.sequencer.initialize()

    async def shutdown(self):
        if self.sequencer is not None:
            await self.sequencer.shutdown()
        if self.on_shutdown:
            await self.on_shutdown()


# ----------------------------------
# PORTS
# ----------------------------------


class Oninitialize(Protocol):
    async def __call__(self) -> None: ...


class OnShutdown(Protocol):
    async def __call__(self) -> None: ...
