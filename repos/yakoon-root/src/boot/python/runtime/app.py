"""
Runtime Host — drives a command coroutine via the shared driver.

Only Python-specific code lives here: module loading and coroutine
validation.  The handler map and drive loop live in ``y5n.base.host``.
"""

import inspect
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
from y5n.base.flow.dsl import Outcome
from y5n.base.flow.primitives import EmitView
from y5n.base.host.driver import drive
from y5n.base.host.handlers import HANDLERS
from y5n.base.host.protocol import MarkerKind


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

    try:
        async for outcome in drive(
            coro,
            HANDLERS,
            side_effects={
                MarkerKind.CWD: lambda path: space.session.set_cwd(path),
            },
        ):
            yield outcome
    except Exception as e:
        yield Outcome(effects=[EmitView(to_text(f"error: {e}"))])

    unload_module(mod_name)
    yield Outcome()
