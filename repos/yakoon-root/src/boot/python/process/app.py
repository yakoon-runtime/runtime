import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from python._shared import build_app_file, resolve_tree_path
from y5n.base.flow.dsl import Outcome
from y5n.base.flow.primitives import EmitView
from y5n.base.projection import to_text


def _emit_text(text: str):
    return EmitView(to_text(text))


async def run(space):
    target_path = space.request.arg(0) if space.request else None
    if not target_path:
        yield Outcome(effects=[EmitView(to_text("Usage: python/process <tree-path>"))])
        return

    root = Path(space.session.get_data("fs:root")) if space.session else Path()
    if not root.is_dir():
        yield Outcome(
            effects=[EmitView(to_text(f"error: workspace root not found: {root}"))]
        )
        return

    current = space.session.get_current_path() if space.session else None
    target_path = resolve_tree_path(target_path, current)

    app_file = build_app_file(root, target_path)
    if app_file is None:
        yield Outcome(
            effects=[
                EmitView(to_text(f"error: no command or script at '{target_path}'"))
            ]
        )
        return

    args = [sys.executable, str(app_file)]
    if space.request:
        for a in space.request.args()[1:]:
            args.append(a)

    try:
        proc = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
    except FileNotFoundError:
        yield Outcome(effects=[EmitView(to_text("error: python not found"))])
        return

    if proc.stdout:
        while True:
            line = await proc.stdout.readline()
            if not line:
                break
            yield Outcome(effects=[_emit_text(line.decode().rstrip())])

    await proc.wait()
    if proc.returncode != 0 and proc.stderr:
        stderr = (await proc.stderr.read()).decode().strip()
        if stderr:
            yield Outcome(effects=[_emit_text(f"error: {stderr}")])

    yield Outcome()
