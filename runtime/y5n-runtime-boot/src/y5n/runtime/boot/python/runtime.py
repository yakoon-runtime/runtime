import asyncio
import importlib
import inspect
import os
from pathlib import Path
from typing import Any

from y5n.runtime.api.flow.dsl import Pulse, out_text
from y5n.runtime.api.runtime.context import current_context

from ._shared import (
    load_and_capture,
    read_entry,
    resolve_tree_path,
    unload_module,
)


async def resolve(node, capability: str, parameters: dict | None = None):
    """The Python host's content interpretation (ADR-10).

    The node's ``resources:`` block owns the pack's strategy (``ref``) and
    the component's content capabilities. The host picks the capability's
    variant, merges its parameters with the resolve-time parameters, and
    interprets the strategy expression — passing ``capability`` and
    ``variant`` so the pack's loader can decide. Legacy top-level
    ``document``/``man`` sections (per-capability refs) stay supported.
    """
    section = node.resources or {}
    ref = section.get("ref")
    if isinstance(ref, str):
        cap_data = section.get(capability)
        if not isinstance(cap_data, dict):
            raise LookupError(f"node '{node.key}' has no '{capability}' resource")
        variant_name, variant_params = _pick_variant(cap_data, parameters)
        merged = {
            "capability": capability,
            "variant": variant_name or "",
            **(variant_params or {}),
            **(parameters or {}),
        }
        return await _interpret(ref, merged, base=node.fs_path)

    # Legacy: per-capability variant map with inline refs.
    cap_data = section.get(capability) or {}
    variant_name, variant = _pick_variant(cap_data, parameters)
    if not variant:
        raise LookupError(f"node '{node.key}' has no '{capability}' resource")
    if isinstance(variant, dict):
        expr = variant.get("ref")
        if not isinstance(expr, str):
            raise LookupError(
                f"node '{node.key}' has no ref expression for '{capability}'"
            )
        merged = {**(variant.get("parameters") or {}), **(parameters or {})}
    else:
        expr = variant
        merged = parameters or {}
    return await _interpret(expr, merged, base=node.fs_path)


def _pick_variant(variants: dict, parameters: dict | None) -> tuple[str | None, Any]:
    """Pick a variant by lang/variant/name hints, then default."""
    params = parameters or {}
    for key in ("lang", "variant", "name"):
        value = params.get(key)
        if value and value in variants:
            return value, variants[value]
    if "default" in variants:
        return "default", variants["default"]
    if variants:
        name = next(iter(variants))
        return name, variants[name]
    return None, None


async def _interpret(expr: str, parameters: dict, base: Path | None):

    scheme, _, value = expr.partition(":")
    if scheme == "file":
        return _file_resource(value, base)
    if scheme == "resource":
        return await _capability_resource(value, parameters)
    raise LookupError(f"unsupported resource expression: {expr!r}")


def _file_resource(value: str, base: Path | None):
    from y5n.runtime.api.resources import Resource

    if not value:
        raise LookupError("file: reference requires a path")
    path = Path(value)
    if path.is_absolute():
        raise LookupError(f"file: reference must be relative: {value!r}")
    if base is None:
        raise LookupError("file: reference requires a base node")
    return Resource.path((base / path).resolve())


async def _capability_resource(value: str, parameters: dict):

    module_name, sep, func_name = value.rpartition(":")
    if not sep or not module_name or not func_name:
        raise LookupError(f"resource: reference must be '<module>:<func>': {value!r}")
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


def _coerce_resource(result):
    from y5n.runtime.api.resources import Resource

    if isinstance(result, Resource):
        return result
    if isinstance(result, str):
        return Resource.text(result)
    if isinstance(result, Path):
        return Resource.path(result)
    raise LookupError(f"capability returned unsupported type: {type(result).__name__}")


async def run():
    ctx = current_context()
    target_path = ctx.get("node", {}).get("path") if ctx else None
    if not target_path:
        yield out_text("Usage: python/runtime <tree-path>")
        return

    root = Path(ctx.get("workspace", "")) if ctx else Path()
    if not root.is_dir():
        yield out_text(f"error: workspace root not found: {root}")
        return

    current = ctx.get("cwd", "") if ctx else None
    target_path = resolve_tree_path(target_path, current)

    entry = read_entry(root, target_path)
    if not entry:
        yield out_text(f"error: no entry for '{target_path}'")
        return

    from ._shared import parse_entry

    try:
        scheme, value = parse_entry(entry)
    except ValueError as e:
        yield out_text(str(e))
        return

    if scheme == "pack":
        os.environ.setdefault("YAK_ENDPOINT", "inprocess://")
        mod_name, _, func_name = value.rpartition(":")
        if not mod_name or not func_name:
            yield out_text(f"error: invalid pack entry '{value}'")
            return
        try:
            mod = importlib.import_module(mod_name)
        except ImportError as e:
            yield out_text(f"error: cannot import {mod_name}: {e}")
            return
        main_fn = getattr(mod, func_name, None)
        if main_fn is None:
            yield out_text(f"error: {mod_name} has no '{func_name}'")
            return
        mod_name_for_cleanup = ""
    elif scheme == "file":
        app_file = root / value
        if not app_file.is_file():
            yield out_text(f"error: file not found: '{app_file}'")
            return

        errors, _, mod, mod_name_for_cleanup = load_and_capture(target_path, app_file)
        if errors:
            for err in errors:
                yield out_text(err)
            return

        main_fn = getattr(mod, "main", None)
        if main_fn is None:
            yield out_text("error: command has no main()")
            return
    else:
        yield out_text(f"error: unknown scheme '{scheme}'")
        return

    coro = main_fn()

    if not inspect.iscoroutine(coro):
        yield out_text(
            "error: main() must be an async function — use `async def main()`"
        )
        return

    # --------------------------------------------------
    # Direct coroutine stepper (replaces drive())
    # --------------------------------------------------

    try:
        gen = coro.__await__()
        val = gen.send(None)

        while True:
            if inspect.iscoroutine(val):
                result = await asyncio.ensure_future(val)
                val = gen.send(result)
                continue

            if isinstance(val, asyncio.Future):
                if val.done():
                    result = val.result()
                else:
                    ev = asyncio.Event()
                    val.add_done_callback(lambda _, ev=ev: ev.set())
                    await ev.wait()
                    result = val.result()
                val = gen.send(result)
                continue

            pulse = val
            if not isinstance(pulse, Pulse):
                raise RuntimeError(
                    f"Unexpected yield from coroutine: {type(pulse).__name__}"
                )

            # Yield upstream to the engine
            event_or_none = yield pulse
            val = gen.send(event_or_none if event_or_none else None)

    except StopIteration:
        pass
    except Exception as e:
        yield out_text(f"error: {e}")

    if mod_name_for_cleanup and mod_name_for_cleanup.startswith("yak.bundle"):
        unload_module(mod_name_for_cleanup)
    yield Pulse()
