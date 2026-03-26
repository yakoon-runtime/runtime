import asyncio
from collections.abc import Awaitable, Callable

from yakoon.base.capabilities.interaction import DialogCancelled
from yakoon.base.ui import View, v_error_system
from yakoon.platform.runtime.devtools.prompt import UnresolvedPromptMonitor
from yakoon.platform.runtime.sessions import Session
from yakoon.platform.settings import settings


class DefaultDialogService:
    """
    Unified input dialog service (view-driven).

    There is exactly one interactive shape:
      - WAITING_INPUT → View (as dict) with optional input definition
    """

    DEFAULT_TIMEOUT = 60 * 15  # 15 minutes

    def __init__(self):
        self._waiting: dict[str, asyncio.Future] = {}
        self._timeouts: dict[str, asyncio.Task] = {}
        self._edges: dict[str, asyncio.Event] = {}

        # pending view payload for the host/runner
        self._views: dict[str, View] = {}

    def is_waiting(self, session: Session) -> bool:
        return str(session.key) in self._waiting

    def edge_event(self, session: Session) -> asyncio.Event:
        session_key = str(session.key)
        ev = self._edges.get(session_key)
        if ev is None:
            ev = asyncio.Event()
            self._edges[session_key] = ev
        return ev

    def get_view(self, session: Session) -> View:
        view = self._views.get(str(session.key))
        if view is None:
            raise RuntimeError("No View available (not waiting for input).")
        return view

    def wait_view(
        self,
        session: Session,
        *,
        view: View,
        timeout: float | None = None,
        on_timeout: Callable[[], Awaitable[None]] | None = None,
    ) -> asyncio.Future:
        """
        Register an input request (View).
        Future resolves with dict[str, object].
        """
        return self._set_waiting(
            session=session,
            view=view,
            timeout=timeout,
            on_timeout=on_timeout,
        )

    def resolve_input(self, session: Session, values: dict[str, object]) -> bool:
        """
        Resolve current input request.
        """
        session_key = str(session.key)
        fut = self._waiting.get(session_key)

        if fut and not fut.done():
            self.cleanup(session)
            fut.set_result(values)
            self.edge_event(session).set()
            return True

        # nothing to resolve; ensure pending view is gone
        self._views.pop(session_key, None)
        return False

    def cancel_input(self, session: Session) -> None:
        session_key = str(session.key)
        fut = self._waiting.get(session_key)

        self.cleanup(session)

        # raise asyncio.CancelledErrornel
        if fut and not fut.done():
            fut.cancel()
            self.edge_event(session).set()

    def resolve_cancelled(self, session: Session) -> None:

        session_key = str(session.key)
        fut = self._waiting.get(session_key)

        self.cleanup(session)

        if fut and not fut.done():
            fut.set_exception(DialogCancelled())
            self.edge_event(session).set()

    def cleanup(self, session: Session) -> None:
        session_key = str(session.key)

        _ = self._waiting.pop(session_key, None)

        task = self._timeouts.pop(session_key, None)
        if task:
            task.cancel()

        self._views.pop(session_key, None)

        if settings.base.dev_mode:
            UnresolvedPromptMonitor.untrack(session_key)

        self.edge_event(session).set()

    def _set_waiting(
        self,
        *,
        session: Session,
        view: View,
        timeout: float | None,
        on_timeout: Callable[[], Awaitable[None]] | None,
    ) -> asyncio.Future:
        session_key = str(session.key)
        fut = asyncio.get_running_loop().create_future()

        if settings.base.dev_mode:
            UnresolvedPromptMonitor.track(session_key, fut)

        self._waiting[session_key] = fut
        self._views[session_key] = view

        self.edge_event(session).set()

        timeout = timeout or settings.network.prompt_timed_out or self.DEFAULT_TIMEOUT

        if timeout:

            async def auto_expire():
                await asyncio.sleep(timeout)
                if not fut.done():
                    self.cleanup(session)
                    fut.cancel()
                    if on_timeout:
                        await on_timeout()
                    else:
                        await session.emit(v_error_system("Input timed out."))

            self._timeouts[session_key] = asyncio.create_task(auto_expire())

        return fut
