from __future__ import annotations

from y5n.kivy.controllers.tabs_controller import TabsController
from y5n.kivy.controllers.tabs_overview_controller import OverviewController
from y5n.kivy.runtime.context import ViewContext
from y5n.kivy.states.tab_state import TabState


class Navigator:

    def __init__(self, app_root):
        self.app_root = app_root

    def go(self, name: str):
        sm = self.app_root.ids.get("sm")
        if sm:
            sm.current = name

    def is_current(self, name: str):
        sm = self.app_root.ids.get("sm")
        return sm and sm.current == name


class AppController:

    def __init__(self, app_root, dispatcher, runner):

        self.app_root = app_root
        self.app_root.set_controller(self)
        self.dispatcher = dispatcher
        self.runner = runner

        # --- STATE ---
        self.tab_state = TabState()

        # --- CONTROLLERS ---
        self.nav = Navigator(app_root)
        self.tabs_ctrl = TabsController(
            self.dispatcher, runner, app_root, self.nav, self.tab_state
        )
        self.overview_ctrl = OverviewController(
            runner, app_root, self.nav, self.tabs_ctrl, self.tab_state
        )

    # --- delegation API (wird von Views/Root benutzt) ---

    def toggle_overview(self):
        if self.nav.is_current("overview"):
            self.show_tabs()
        else:
            self.show_overview()

    def show_overview(self):
        self.nav.go("overview")
        self.overview_ctrl.open()
        self.current = self.overview_ctrl

    def show_tabs(self):
        self.nav.go("tabs")
        self.tabs_ctrl.focus_active()
        self.current = self.tabs_ctrl

    def new_chat_tab(self, select: bool = True) -> str:
        return self.tabs_ctrl.new_chat_tab(select=select)

    def select_tab(self, tab_id: str):
        self.tabs_ctrl.select(tab_id)

    def close_tab(self, tab_id: str):
        self.tabs_ctrl.close(tab_id)
        # falls overview offen ist: sinnvoll refreshen
        self.overview_ctrl.refresh()

    # --- output routing ---
    def dispatch_context(self, ctx: ViewContext) -> None:
        if getattr(ctx.session, "has_signal", None) and ctx.session.has_signal(
            "exit_app"
        ):
            if hasattr(self.app_root, "stop_app"):
                self.app_root.stop_app()
            return

        page = self.tabs_ctrl.active_page()
        if page and hasattr(page, "apply_context"):
            page.apply_context(ctx)
