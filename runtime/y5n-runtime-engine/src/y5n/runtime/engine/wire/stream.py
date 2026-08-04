from y5n.runtime.engine.document.transport import (
    EventDispatcher,
    EventFactory,
    EventStreamOutput,
    EventTraversal,
)


def build_stream() -> EventStreamOutput:

    factory = EventFactory()
    traversal = EventTraversal()

    dispatcher = EventDispatcher(
        factory=factory,
        traversal=traversal,
    )

    return EventStreamOutput(
        on_begin=dispatcher.begin_projection,
        on_emit=dispatcher.emit_projection,
        on_abort=dispatcher.abort_projection,
        on_finish=dispatcher.finish_projection,
    )
