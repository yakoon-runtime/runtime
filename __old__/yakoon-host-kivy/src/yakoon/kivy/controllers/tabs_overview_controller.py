from y5n.kivy.states.tab_state import TabState


class OverviewController:

    def __init__(self, runner, app_root, navigator, tabs_ctrl, state: TabState):

        self.runner = runner
        self.app_root = app_root
        self.nav = navigator
        self.tabs = tabs_ctrl
        self.state = state

    def open(self):
        page = self.app_root.ids.get("overview_page")
        if page:
            page.set_controller(self)
            page.render(self.state.tabs)
        self.nav.go("overview")

    def refresh(self):
        page = self.app_root.ids.get("overview_page")
        if page and hasattr(page, "render"):
            page.render(self.state.tabs)

    # Callbacks für TabOverviewPage:
    def on_open_tab(self, tab_id: str):
        self.tabs.select(tab_id)

    def on_close_tab(self, tab_id: str):
        self.tabs.close(tab_id)
        self.refresh()

    def on_new_tab(self):
        self.tabs.new_chat_tab(select=True)
        self.refresh()
