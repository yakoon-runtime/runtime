"""dotnet/process host: run .NET assemblies or native binaries."""
import asyncio
from pathlib import Path

import yaml

from y5n.base.flow.dsl import Outcome
from y5n.base.flow.primitives import EmitView
from y5n.base.projection import to_text


async def run(space):
    target_path = space.request.arg(0) if space.request else None
    if not target_path:
        yield Outcome(effects=[EmitView(to_text("Usage: dotnet/process <tree-path>"))])
        return

    root = Path(space.session.get_data("fs:root")) if space.session else Path()
    if not root.is_dir():
        yield Outcome(
            effects=[EmitView(to_text(f"error: workspace root not found: {root}"))]
        )
        return

    rel = target_path.strip("/")
    cmd_dir = root / rel
    yak_meta = cmd_dir / "_yak" / "yak.yml"
    if not yak_meta.is_file():
        yield Outcome(
            effects=[EmitView(to_text(f"error: no yak.yml at '{target_path}'"))]
        )
        return

    with open(yak_meta) as f:
        meta = yaml.safe_load(f) or {}
    entry = meta.get("entry", {}).get("run")
    if not entry:
        yield Outcome(
            effects=[EmitView(to_text(f"error: no entry.run in '{target_path}'"))]
        )
        return

    app_file = cmd_dir / entry
    if not app_file.is_file():
        yield Outcome(
            effects=[EmitView(to_text(f"error: entry file not found: {app_file}"))]
        )
        return

    ext = app_file.suffix.lower()
    if ext == ".dll":
        args = ["dotnet", str(app_file)]
    elif ext == "" or ext == ".exe":
        args = [str(app_file)]
    else:
        yield Outcome(
            effects=[EmitView(to_text(f"error: unknown entry type: {entry}"))]
        )
        return

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
        yield Outcome(effects=[EmitView(to_text("error: dotnet not found"))])
        return

    if proc.stdout:
        while True:
            line = await proc.stdout.readline()
            if not line:
                break
            yield Outcome(effects=[EmitView(to_text(line.decode().rstrip()))])

    stderr_text = ""
    if proc.stderr:
        stderr_text = (await proc.stderr.read()).decode().strip()

    await proc.wait()
    if proc.returncode != 0:
        msg = stderr_text or f"error: process exited with code {proc.returncode}"
        yield Outcome(effects=[EmitView(to_text(msg))])

    yield Outcome()
