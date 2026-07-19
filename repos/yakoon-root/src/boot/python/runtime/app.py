"""
Runtime Host — drives a command coroutine directly via send(None).

Marker protocol (from y5n.sdk.runtime):

    ('write', view)           → out(view, mode=...)
    ('error', text)           → out({"kind": "error", "text": text})
    ('delay', seconds)         → delay(seconds)
    ('delay_until', ts)        → delay_until(ts)
    ('view', params)           → view(**params)
"""

import inspect
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from python._shared import (
    build_app_file,
    load_and_capture,
    resolve_tree_path,
    unload_module,
)
from y5n.base.document import to_text
from y5n.base.flow.dsl import Outcome, delay, delay_until, out
from y5n.base.flow.dsl import view as dsl_view
from y5n.base.flow.primitives import EmitView


def _resolve_view(view: dict | str) -> dict:
    if isinstance(view, dict):
        return view
    if view.startswith("{"):
        try:
            data = json.loads(view)
            if isinstance(data, dict) and data.get("kind") == "document":
                return data
        except Exception:
            pass
    return to_text(view)


async def run(space):
    target_path = space.request.arg(0) if space.request else None
    if not target_path:
        yield Outcome(effects=[EmitView(to_text("Usage: python/runtime <tree-path>"))])
        return

    root = Path(space.session.get_data("fs:root")) if space.session else Path()
    if not root.is_dir():
        yield Outcome(
            effects=[EmitView(to_text(f"error: workspace root not found: {root}"))]
        )
        return

    current = space.session.cwd if space.session else None
    target_path = resolve_tree_path(target_path, current)

    app_file = build_app_file(root, target_path)
    if app_file is None:
        yield Outcome(
            effects=[
                EmitView(to_text(f"error: no command or script at '{target_path}'"))
            ]
        )
        return

    errors, _, mod, mod_name = load_and_capture(space, target_path, app_file)
    if errors:
        for err in errors:
            yield Outcome(effects=[EmitView(to_text(err))])
        return

    main_fn = getattr(mod, "main", None)
    if main_fn is None:
        yield Outcome(effects=[EmitView(to_text("error: command has no main()"))])
        return

    coro = main_fn()

    if not inspect.iscoroutine(coro):
        yield Outcome(
            effects=[
                EmitView(
                    to_text(
                        "error: main() must be an async function"
                        " — use `async def main()`"
                    )
                )
            ]
        )
        return

    first_output = True
    try:
        marker = coro.send(None)
        while True:
            kind, value = marker

            if kind == "write":
                view = _resolve_view(value)
                mode = "replace" if first_output else "append"
                first_output = False
                yield out(view, mode=mode)
                marker = coro.send(None)

            elif kind == "error":
                yield out({"kind": "error", "text": value})
                marker = coro.send(None)

            elif kind == "delay":
                yield delay(value)
                marker = coro.send(None)

            elif kind == "delay_until":
                yield delay_until(value)
                marker = coro.send(None)

            elif kind == "view":
                yield dsl_view(**value)
                marker = coro.send(None)

            else:
                marker = coro.send(None)

    except StopIteration:
        pass
    except Exception as e:
        yield Outcome(effects=[EmitView(to_text(f"error: {e}"))])

    unload_module(mod_name)
    yield Outcome()
