"""Python Host — loads and runs a Python command or bare script.

Invocation:
    python-host <tree-path>

Supports two modes:
  1. Command: <path>/_yak/run/app.py with main() or async main()
  2. Script:  <path>.py — top-level code runs on load, optional main()
"""

import importlib.util
import inspect
import os
import sys
from pathlib import Path

from y5n.base.flow.dsl import Outcome
from y5n.base.flow.primitives import EmitView
from y5n.base.projection import to_text
from y5n.base.runtime.context import CommandContext, _set_context


def _resolve_tree_path(tree_path: str, current_path: str | None) -> str:
    """Resolve a possibly relative tree path against the current path.

    If tree_path starts with \"/\", it is absolute and returned as-is.
    Otherwise it is resolved relative to the current node's path
    (e.g. \"hello-client\" from \"/usr/bin\" → \"/usr/bin/hello-client\").
    """
    if tree_path.startswith("/"):
        return tree_path
    current_path = (current_path or "").strip("/")
    if current_path:
        combined = current_path + "/" + tree_path.lstrip("/")
    else:
        combined = tree_path.lstrip("/")
    return "/" + os.path.normpath(combined)


def _find_command(root: Path, tree_path: str) -> Path | None:
    """Find a structured command at <tree_path>/_yak/run/app.py."""
    rel = tree_path.strip("/")
    candidate = root / rel
    if (candidate / "_yak" / "run" / "app.py").is_file():
        return candidate
    return None


def _find_script(root: Path, tree_path: str) -> Path | None:
    """Find a bare .py file at <tree_path> (absolute or under root)."""
    p = Path(tree_path)
    if p.is_file() and p.suffix == ".py":
        return p
    rel = tree_path.strip("/")
    candidate = root / rel
    if candidate.is_file() and candidate.suffix == ".py":
        return candidate
    return None


async def _run_main(mod):
    """Call main() or async main() and return captured stdout."""
    from contextlib import redirect_stdout
    from io import StringIO

    if not hasattr(mod, "main"):
        return ""

    main_fn = mod.main
    buf = StringIO()
    if inspect.iscoroutinefunction(main_fn):
        with redirect_stdout(buf):
            await main_fn()
    else:
        with redirect_stdout(buf):
            main_fn()
    return buf.getvalue()


async def run(space):
    target_path = space.request.arg(0) if space.request else None
    if not target_path:
        yield Outcome(effects=[EmitView(to_text("Usage: python-host <tree-path>"))])
        return

    root = Path(space.session.get_data("fs:root")) if space.session else Path()
    if not root.is_dir():
        yield Outcome(effects=[EmitView(to_text(f"error: workspace root not found: {root}"))])
        return

    # Resolve relative tree paths against session's current path
    current = space.session.get_current_path() if space.session else None
    target_path = _resolve_tree_path(target_path, current)

    # Try command mode first, then script mode
    bundle_dir = _find_command(root, target_path)
    if bundle_dir is not None:
        app_file = bundle_dir / "_yak" / "run" / "app.py"
        segments = [s for s in target_path.strip("/").split("/") if s]
        mod_name = "hosted." + ".".join(segments) + ".app"
    else:
        script = _find_script(root, target_path)
        if script is None:
            yield Outcome(effects=[EmitView(to_text(f"error: no command or script at '{target_path}'"))])
            return
        app_file = script
        mod_name = "hosted.script." + app_file.stem

    spec = importlib.util.spec_from_file_location(mod_name, app_file)
    if spec is None or spec.loader is None:
        yield Outcome(effects=[EmitView(to_text(f"error: cannot load {app_file}"))])
        return

    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)

    # Build context for the hosted program
    node_name = target_path.rsplit("/", 1)[-1] if target_path else ""
    _set_context(
        CommandContext(
            path=target_path,
            command=node_name,
            tokens=space.request.args()[1:] if space.request and space.request.args() else [],
            session={
                "key": str(space.session.key) if space.session else None,
                "lang": space.session.lang if space.session else None,
            },
        )
    )

    output = await _run_main(mod)

    if output:
        for line in output.splitlines():
            yield Outcome(effects=[EmitView(to_text(line), mode="append")])

    yield Outcome()
