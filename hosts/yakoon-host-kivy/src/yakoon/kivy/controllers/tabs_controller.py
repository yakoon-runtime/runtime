from kivy.clock import Clock
from yakoon.base.capabilities.identity import PermissionService
from yakoon.base.naming import Key
from yakoon.base.runtime.sessions import SessionStore
from yakoon.kivy.host import KivyHost
from yakoon.kivy.runner import SessionRunner
from yakoon.kivy.runtime.output.output import KivyOutput
from yakoon.kivy.states.state_provider import UIStateProvider
from yakoon.kivy.states.tab_state import TabRuntime, TabState
from yakoon.kivy.thread import TabRunnerThread
from yakoon.kivy.widgets.commands.surface import CommandSurface


class TabsController:

    def __init__(
        self, dispatcher, runner: SessionRunner, app_root, navigator, state: TabState
    ):

        self.dispatcher = dispatcher
        self.runner = runner
        self.app_root = app_root
        self.nav = navigator
        self.state = state

    def new_chat_tab(self, select: bool = True) -> str:
        self.state.counter += 1
        tab_id = f"chat-{self.state.counter}"
        title = "chat" if self.state.counter == 1 else f"chat {self.state.counter}"

        page = CommandSurface(self.on_chat_submit)
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
        sessions = self.runner.engine.services.get(SessionStore)
        perms = self.runner.engine.services.get(PermissionService)

        tab_id = f"kivy:tab:{tab_id}"
        session_key = Key.from_parts("system", "session", tab_id, "1")
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

        runtime = self.state.runtimes.pop(tab_id, None)
        if runtime and runtime.runner_thread:
            runtime.runner_thread.stop()

        self.state.pages.pop(tab_id, None)
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

        output = KivyOutput(
            session=session,
            on_context=self.dispatcher,
            ui_state_provider=UIStateProvider(session),
        )
        session.bind_io(output)

        # Pro Tab: eigener Host + eigener RunnerThread
        page = self.state.pages[tab_id]  # das ChatWidget für diesen Tab
        host = KivyHost(submit=lambda _evt: None, ui=page)

        runner_thread = TabRunnerThread(
            engine=self.runner.engine, session=session, host=host, inits=[]
        )
        runner_thread.start()

        self.state.runtimes[tab_id] = TabRuntime(
            tab_id=tab_id,
            session=session,
            host=host,
            runner_thread=runner_thread,
        )

    def on_chat_submit(self, text: str):
        tab_id = self.state.active_tab_id
        runtime = self.state.runtimes.get(tab_id)
        if not runtime:
            return

        loop = runtime.runner_thread.loop if runtime.runner_thread else None
        if not loop:
            return

        runtime.host.deliver_text(loop=loop, text=text)
