from collections.abc import Iterator

from yakoon.base.ui.event import ViewEvent
from yakoon.base.ui.view import View
from yakoon.platform.ui.builder.emitter import ViewEmitter
from yakoon.platform.ui.builder.traversal import ViewTraversal


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

        # starts the protocol
        yield self.emitter.begin(view.id)

        # emit all operations.
        ops = list(self.traversal.iter_ops(view))
        yield self.emitter.emit(view.id, ops)

        ## ends the protocol.
        yield self.emitter.finish(view.id)
