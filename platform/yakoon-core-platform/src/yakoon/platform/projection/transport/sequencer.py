from collections.abc import Iterator

from yakoon.base.projection import Projection, ProjectionEvent
from yakoon.platform.projection.builder.emitter import ViewEmitter
from yakoon.platform.projection.builder.traversal import ViewTraversal


class ViewSequencer:

    def __init__(self):
        self.traversal = ViewTraversal()
        self.emitter = ViewEmitter()

    def sequence(self, projection: Projection) -> Iterator[ProjectionEvent]:
        """
        Produces a complete, batched ViewEvent sequence:
        BEGIN → FULL PATCH → FINISH
        """

        if not projection.id:
            raise RuntimeError("Projection must have id.")
        if not projection.header:
            raise RuntimeError("Projection must have an header.")

        # starts the protocol
        yield self.emitter.begin(projection.header, projection.id)

        # emit all operations.
        ops = list(self.traversal.iter_ops(projection))
        yield self.emitter.emit(projection.id, ops)

        ## ends the protocol.
        yield self.emitter.finish(projection.id)
