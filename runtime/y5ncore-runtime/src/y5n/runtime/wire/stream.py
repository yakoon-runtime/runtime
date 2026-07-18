from y5n.runtime.document.transport import (
    EventDispatcher,
    EventFactory,
    EventStreamOutput,
    EventTraversal,
)


def build_stream() -> EventStreamOutput:

    # --- BUILDING ---

    factory = EventFactory()

    # --- TRAVERSALING ---

    traversal = EventTraversal()

    # --- DISPATCHING ---

    dispatcher = EventDispatcher(
        on_create_begin_event=factory.begin_event,
        on_create_batch_event=factory.patch_event,
        on_create_finish_event=factory.finish_event,
        on_get_traversal_root=traversal.root_id,
        on_get_traversal_parent=traversal.resolve_parent,
        on_get_traversal_prepare=traversal.prepare_block,
    )

    # --- STREAMING ---

    return EventStreamOutput(
        on_begin=dispatcher.begin_projection,
        on_emit=dispatcher.emit_projection,
        on_abort=dispatcher.abort_projection,
        on_finish=dispatcher.finish_projection,
    )
