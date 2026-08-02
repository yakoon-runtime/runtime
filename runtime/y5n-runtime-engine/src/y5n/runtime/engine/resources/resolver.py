"""In-process Python resource resolver (ADR-10).

Resolves the reference schemes a Python host supports:

* ``file:<path>``              — a file relative to the declaring node
* ``resource:<module>:<func>`` — a capability: import the module, call the
  function, expect a ``Resource`` (or a coercible ``str``/``Path``).

The host owns scheme names and reference values; the runtime never interprets
them. This resolver is the in-process realization of the Python host behind
the ``runtime.resource`` service.
"""

from __future__ import annotations

import importlib
import inspect
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from y5n.runtime.api.resources import Resource

_SCHEMES = frozenset({"file", "resource"})


class PythonResourceResolver:
    """The in-process Python host's resolver behind ``runtime.resource``."""

    def supports(self, ref: str) -> bool:
        """Whether this host can resolve the given reference."""
        return ref.split(":", 1)[0] in _SCHEMES

    async def resolve(
        self,
        ref: str,
        *,
        parameters: Mapping[str, Any] | None = None,
        base: Path | None = None,
    ) -> Resource:
        """Resolve a reference into a ``Resource``.

        ``base`` is the declaring node's structure directory, required by the
        ``file:`` scheme.
        """
        scheme, _, value = ref.partition(":")
        if scheme == "file":
            return self._resolve_file(value, base)
        if scheme == "resource":
            return await self._resolve_capability(value, parameters or {})
        raise LookupError(f"unsupported resource reference: {ref!r}")

    def _resolve_file(self, value: str, base: Path | None) -> Resource:
        if not value:
            raise LookupError("file: reference requires a path")
        path = Path(value)
        if path.is_absolute():
            raise LookupError(f"file: reference must be relative: {value!r}")
        if base is None:
            raise LookupError("file: reference requires a base node")
        return Resource.path((base / path).resolve())

    async def _resolve_capability(
        self,
        value: str,
        parameters: Mapping[str, Any],
    ) -> Resource:
        module_name, sep, func_name = value.rpartition(":")
        if not sep or not module_name or not func_name:
            raise LookupError(
                f"resource: reference must be '<module>:<func>': {value!r}"
            )
        try:
            module = importlib.import_module(module_name)
        except ImportError as exc:
            raise LookupError(f"cannot import module {module_name!r}") from exc
        fn = getattr(module, func_name, None)
        if fn is None or not callable(fn):
            raise LookupError(f"no capability {func_name!r} in module {module_name!r}")
        result = fn(**parameters)
        if inspect.isawaitable(result):
            result = await result
        return _coerce_resource(result)


def _coerce_resource(result: Any) -> Resource:
    if isinstance(result, Resource):
        return result
    if isinstance(result, str):
        return Resource.text(result)
    if isinstance(result, Path):
        return Resource.path(result)
    raise LookupError(f"capability returned unsupported type: {type(result).__name__}")
