from __future__ import annotations

from yakoon.base.ui.view_spec import ViewSpec
from yakoon.kivy.runtime.context.view_context import ViewContext
from yakoon.kivy.runtime.output.output_adapter import OutputAdapter


class KivyOutput:
    def __init__(self, *, session, on_context, ui_state_provider):
        self._session = session
        self._on_context = on_context
        self._ui_state_provider = ui_state_provider

    async def view(self, view: ViewSpec) -> None:
        ctx = ViewContext(
            session=self._session,
            envelope=view,
            ui_state_provider=self._ui_state_provider,
        )
        self._on_context(ctx)


class SessionBoundKivyOutput(OutputAdapter):
    def __init__(self, session, kivy_output: KivyOutput):
        # OutputAdapter erwartet emit_fn / emit_err_fn (sync oder async)
        super().__init__(
            emit_fn=lambda evt: kivy_output.emit(session, evt),
            emit_err_fn=lambda evt: kivy_output.emit(session, evt),
        )
