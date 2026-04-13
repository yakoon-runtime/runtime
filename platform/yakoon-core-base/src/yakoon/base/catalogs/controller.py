from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import ControllerInfo


class ControllerCatalog:

    def __init__(self, controllers: Iterable[ControllerInfo]):
        self._controllers = controllers

    def all(self):
        return self._controllers
