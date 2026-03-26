from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from yakoon.base.capabilities.presenters import PresenterView
    from yakoon.base.ui.view import View


class Operations:

    def __init__(self, command):
        self._cmd = command

    # -------------------------
    # ask
    # -------------------------
    def ask(self, view: View | PresenterView):
        return ask(view)

    # -------------------------
    # show
    # -------------------------
    def show(self, view: View | PresenterView):
        return show(view)  # oder show(view)
