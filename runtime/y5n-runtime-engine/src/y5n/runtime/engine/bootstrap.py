"""Bootstrap reference linking (ADR-10).

The runtime resolves ``pack:<module>:<func>`` for exactly one purpose:
loading the first host. This is *linking*, not interpretation — the runtime
loads the declared function but does not understand what the reference
means. Every later reference expression is interpreted by the host.

The linker is shared by the runtime executor (which runs host nodes that
have no host of their own) and by the tree (which builds a host node's
``resolve`` handler from its ``resolve:`` declaration).
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any


class PackReference:
    """A ``pack:<module>:<func>`` bootstrap reference.

    The expression is parsed eagerly (string split, no import). The function
    is loaded lazily on the first ``load()`` call, so building the tree never
    imports host modules (ADR-10).
    """

    __slots__ = ("_module", "_func")

    def __init__(self, expr: str):
        scheme, _, value = expr.partition(":")
        if scheme != "pack":
            raise ValueError(f"invalid pack reference: {expr!r}")
        module, sep, func = value.rpartition(":")
        if not sep or not module or not func:
            raise ValueError(f"invalid pack reference: {expr!r}")
        self._module = module
        self._func = func

    def load(self) -> Callable[..., Any]:
        import importlib

        try:
            module = importlib.import_module(self._module)
        except ImportError as exc:
            raise LookupError(f"cannot import module {self._module!r}") from exc
        fn = getattr(module, self._func, None)
        if fn is None or not callable(fn):
            raise LookupError(f"no function {self._func!r} in module {self._module!r}")
        return fn
