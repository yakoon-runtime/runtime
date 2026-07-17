"""Shared helpers for Python hosts (runtime, thread, process).

Each host provides its own execution strategy via _run_main().
Everything else (resolve, load, context, output) lives here.
"""

import importlib.util
import os
import sys
import uuid
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

import yaml
from y5n.base.flow.dsl import Outcome
from y5n.base.flow.primitives import EmitView
from y5n.base.projection import to_text
from y5n.base.runtime.context import CommandContext, _set_context


def _read_yak_meta(dir_path: Path) -> dict:
    yak_file = dir_path / "_yak" / "yak.yml"
    if yak_file.is_file():
        with open(yak_file) as f:
            return yaml.safe_load(f) or {}
    return {}


def resolve_tree_path(tree_path: str, current_path: str | None) -> str:
    if tree_path.startswith("/"):
        return tree_path
    current_path = (current_path or "").strip("/")
    if current_path:
        combined = current_path + "/" + tree_path.lstrip("/")
    else:
        combined = tree_path.lstrip("/")
    return "/" + os.path.normpath(combined)


def find_command(root: Path, tree_path: str) -> Path | None:
    rel = tree_path.strip("/")
    candidate = root / rel
    meta = _read_yak_meta(candidate)
    entry = meta.get("entry", {}).get("run") if meta else None
    if entry and (candidate / entry).is_file():
        return candidate
    return None


def find_script(root: Path, tree_path: str) -> Path | None:
    p = Path(tree_path)
    if p.is_file() and p.suffix == ".py":
        return p
    rel = tree_path.strip("/")
    candidate = root / rel
    if candidate.is_file() and candidate.suffix == ".py":
        return candidate
    return None


def build_app_file(root: Path, target_path: str) -> Path | None:
    """Resolve target_path to an app.py or .py file. Returns None on error."""
    bundle_dir = find_command(root, target_path)
    if bundle_dir is not None:
        meta = _read_yak_meta(bundle_dir)
        entry = meta.get("entry", {}).get("run", "")
        return bundle_dir / entry if entry else None
    script = find_script(root, target_path)
    if script is not None:
        return script
    return None


def load_and_capture(
    space,
    target_path: str,
    app_file: Path,
) -> tuple[list[str], str]:
    """Set context, load module, capture stdout from import.

    Returns (error_messages, captured_stdout) where error_messages
    is empty on success or a list of error lines.
    """
    mod_name = f"hosted.{uuid.uuid4().hex}"
    spec = importlib.util.spec_from_file_location(mod_name, app_file)
    if spec is None or spec.loader is None:
        return [f"error: cannot load {app_file}"], ""

    node_name = target_path.rsplit("/", 1)[-1] if target_path else ""
    _set_context(
        CommandContext(
            path=target_path,
            command=node_name,
            tokens=(
                list(space.request.args())[1:]
                if space.request and space.request.args()
                else []
            ),
            session={
                "key": str(space.session.key) if space.session else None,
                "lang": space.session.lang if space.session else None,
            },
        )
    )

    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    buf = StringIO()
    with redirect_stdout(buf):
        spec.loader.exec_module(mod)

    return [], buf.getvalue(), mod


def emit_output(output: str) -> list:
    """Return Outcome list from captured stdout."""
    if not output:
        return []
    return [
        Outcome(effects=[EmitView(to_text(line), mode="append")])
        for line in output.splitlines()
    ]
