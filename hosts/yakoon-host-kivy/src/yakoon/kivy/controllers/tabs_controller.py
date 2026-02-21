from kivy.clock import Clock
from yakoon.base.ports import PermissionService, SessionService
from yakoon.kivy.runtime.output.output import KivyOutput, SessionBoundKivyOutput
from yakoon.kivy.states.state_provider import UIStateProvider
from yakoon.kivy.states.tab_state import TabRuntime, TabState
from yakoon.kivy.widgets.chat.chat_widget import ChatWidget


class TabsController:

    def __init__(self, dispatcher, runner, app_root, navigator, state: TabState):

        self.dispatcher = dispatcher
        self.runner = runner
        self.app_root = app_root
        self.nav = navigator
        self.state = state

    def new_chat_tab(self, select: bool = True) -> str:
        self.state.counter += 1
        tab_id = f"chat-{self.state.counter}"
        title = "chat" if self.state.counter == 1 else f"chat {self.state.counter}"

        page = ChatWidget(self.on_chat_submit)
        self.state.tabs.append({"id": tab_id, "title": title})
        self.state.pages[tab_id] = page

        task = self.runner.submit_coro(self._create_tab_session(tab_id))
        task.add_done_callback(
            lambda t: Clock.schedule_once(
                lambda _dt: self._on_session_ready(tab_id, t), 0
            )
        )

        if select or self.state.active_tab_id is None:
            self.select(tab_id)
        else:
            self._refresh_tabs()

        return tab_id

    async def _create_tab_session(self, tab_id: str):
        sessions = self.runner.engine.services.get(SessionService)
        perms = self.runner.engine.services.get(PermissionService)

        session_key = f"kivy:tab:{tab_id}"
        session, _ = await sessions.get_or_create(session_key)
        perms.set_bootstrap_permissions(session)

        return session

    def _refresh_tabs(self):
        tabbar = self.app_root.ids.get("tabbar")
        if tabbar:
            tabbar.set_tabs(
                self.state.tabs, self.state.active_tab_id, on_select=self.select
            )

    def select(self, tab_id: str):
        if tab_id not in self.state.pages:
            return

        self.state.active_tab_id = tab_id
        self._refresh_tabs()

        self.nav.go("tabs")
        tabs_page = self.app_root.ids.get("tabs_page")
        if tabs_page and hasattr(tabs_page, "set_content"):
            tabs_page.set_content(self.state.pages[tab_id])

        self.focus_active()

    def close(self, tab_id: str):
        if tab_id not in self.state.pages:
            return

        self.state.pages.pop(tab_id, None)
        self.state.runtimes.pop(tab_id, None)
        self.state.tabs = [t for t in self.state.tabs if t["id"] != tab_id]

        if self.state.active_tab_id == tab_id:
            self.state.active_tab_id = (
                self.state.tabs[0]["id"] if self.state.tabs else None
            )
            if self.state.active_tab_id:
                self.select(self.state.active_tab_id)
            else:
                self.nav.go("overview")

        self._refresh_tabs()

    def focus_active(self):
        page = self.state.pages.get(self.state.active_tab_id)
        if page and hasattr(page, "focus_prompt"):
            page.focus_prompt()

    def active_page(self):
        return self.state.pages.get(self.state.active_tab_id)

    def _on_session_ready(self, tab_id: str, task):
        session = task.result()

        self.state.runtimes[tab_id] = TabRuntime(tab_id=tab_id, session=session)

        output = KivyOutput(
            on_context=self.dispatcher, ui_state_provider=UIStateProvider(session)
        )

        session.bind_io(SessionBoundKivyOutput(session, output))

    def on_chat_submit(self, text: str):
        tab_id = self.state.active_tab_id
        runtime = self.state.runtimes.get(tab_id)
        if not runtime:
            return

        self.runner.enqueue(runtime.session, text)
