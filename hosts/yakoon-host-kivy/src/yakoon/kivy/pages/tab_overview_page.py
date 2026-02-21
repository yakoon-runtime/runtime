# yakoon/kivy/pages/tab_overview_page.py
from __future__ import annotations

from kivy.factory import Factory
from kivy.properties import NumericProperty, ObjectProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout


class TabOverviewPage(BoxLayout):

    title = StringProperty("Tabs")
    tab_count = NumericProperty(0)
    controller = ObjectProperty(allownone=True)

    def set_controller(self, controller):
        self.controller = controller

    def render(self, tabs):
        self.tab_count = len(tabs)
        grid = self.ids.grid
        grid.clear_widgets()
        for t in tabs:
            card = self._make_card(t["id"], t["title"])
            grid.add_widget(card)

    def _make_card(self, tab_id: str, title: str):

        card = Factory.TabCard()
        card.tab_id = tab_id
        card.title = title

        card.bind(on_open=lambda _w, tab_id: self._open(tab_id))
        card.bind(on_close=lambda _w, tab_id: self._close(tab_id))

        return card

    def _open(self, tab_id: str):
        if self.controller:
            self.controller.on_open_tab(tab_id)

    def _close(self, tab_id: str):
        if self.controller:
            self.controller.on_close_tab(tab_id)

    def on_new_tab(self):
        if self.controller:
            self.controller.on_new_tab()


Factory.register("TabOverviewPage", cls=TabOverviewPage)
