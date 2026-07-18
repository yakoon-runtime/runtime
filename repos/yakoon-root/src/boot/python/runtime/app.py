import inspect
import sys
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from python._shared import (
    build_app_file,
    emit_output,
    load_and_capture,
    resolve_tree_path,
    unload_module,
)
from y5n.base.document import to_text
from y5n.base.flow.dsl import Outcome
from y5n.base.flow.primitives import EmitView


async def _run_main(mod):
    if not hasattr(mod, "main"):
        return "", ""
    main_fn = mod.main
    buf = StringIO()
    err_buf = StringIO()
    with redirect_stdout(buf), redirect_stderr(err_buf):
        if inspect.iscoroutinefunction(main_fn):
            await main_fn()
        else:
            main_fn()
    return buf.getvalue(), err_buf.getvalue()


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

    errors, import_output, mod, mod_name = load_and_capture(
        space, target_path, app_file
    )
    if errors:
        for err in errors:
            yield Outcome(effects=[EmitView(to_text(err))])
        return

    for outcome in emit_output(import_output):
        yield outcome

    main_output, main_errors = await _run_main(mod)
    if main_errors:
        for line in main_errors.splitlines():
            yield Outcome(effects=[EmitView(to_text(f"error: {line}"), mode="append")])
    for outcome in emit_output(main_output):
        yield outcome

    unload_module(mod_name)

    yield Outcome()
