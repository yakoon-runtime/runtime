import asyncio
import inspect
import sys
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from python._shared import (
    build_app_file,
    emit_output,
    load_and_capture,
    resolve_tree_path,
)
from y5n.base.flow.dsl import Outcome
from y5n.base.flow.primitives import EmitView
from y5n.base.projection import to_text


async def _run_main(mod):
    if not hasattr(mod, "main"):
        return ""
    main_fn = mod.main
    if inspect.iscoroutinefunction(main_fn):
        buf = StringIO()
        with redirect_stdout(buf):
            await main_fn()
        return buf.getvalue()
    loop = asyncio.get_running_loop()
    buf = StringIO()
    with redirect_stdout(buf):
        await loop.run_in_executor(None, main_fn)
    return buf.getvalue()


async def run(space):
    target_path = space.request.arg(0) if space.request else None
    if not target_path:
        yield Outcome(effects=[EmitView(to_text("Usage: python/thread <tree-path>"))])
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

    errors, import_output, mod = load_and_capture(space, target_path, app_file)
    if errors:
        for err in errors:
            yield Outcome(effects=[EmitView(to_text(err))])
        return

    for outcome in emit_output(import_output):
        yield outcome

    main_output = await _run_main(mod)
    for outcome in emit_output(main_output):
        yield outcome

    yield Outcome()
