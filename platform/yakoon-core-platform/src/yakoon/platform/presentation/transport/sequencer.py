from collections.abc import Iterator

from yakoon.base.presentation import View, ViewEvent
from yakoon.platform.presentation.builder.emitter import ViewEmitter
from yakoon.platform.presentation.builder.traversal import ViewTraversal


class ViewSequencer:

    def __init__(self):
        self.traversal = ViewTraversal()
        self.emitter = ViewEmitter()

    def sequence(self, view: View) -> Iterator[ViewEvent]:
        """
        Produces a complete, batched ViewEvent sequence:
        BEGIN → FULL PATCH → FINISH
        """

        if not view.id:
            raise RuntimeError("View must have id.")
        if not view.header:
            raise RuntimeError("View must have an header.")

        # starts the protocol
        yield self.emitter.begin(view.header, view.id)

        # emit all operations.
        ops = list(self.traversal.iter_ops(view))
        yield self.emitter.emit(view.id, ops)

        ## ends the protocol.
        yield self.emitter.finish(view.id)
