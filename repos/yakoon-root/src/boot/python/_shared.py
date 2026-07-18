"""Shared helpers for Python hosts (runtime, thread, process).

Each host provides its own execution strategy via _run_main().
Everything else (resolve, load, context, output) lives here.
"""

import importlib.util
import json as _json
import os
import sys
import uuid
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from typing import Any

import yaml
from y5n.base.document import to_text
from y5n.base.flow.dsl import Outcome
from y5n.base.flow.primitives import EmitView
from y5n.sdk import context as sdk_context
from y5n.sdk.libs.models import Context as SdkContext


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


def _build_context_dict(space, target_path: str) -> dict:
    """Build a Context JSON dict from a Runtime space object."""
    node_name = target_path.rsplit("/", 1)[-1] if target_path else ""
    workspace = space.session.get_data("fs:root") if space.session else ""

    return {
        "node": {
            "path": target_path,
            "name": node_name,
        },
        "cwd": space.session.cwd if space.session else "",
        "workspace": str(workspace) if workspace else "",
        "user": {
            "id": str(space.session.key) if space.session else None,
            "name": space.session.user_name if space.session else None,
        },
        "session": {
            "key": str(space.session.key) if space.session else None,
            "lang": space.session.lang if space.session else None,
            "interaction": space.session.interaction.value if space.session else None,
        },
        "tokens": (
            list(space.request.args())
            if space.request and space.request.args()
            else []
        ),
    }


def load_and_capture(
    space,
    target_path: str,
    app_file: Path,
) -> tuple[list[str], str, Any, str]:
    """Set context, load module, capture stdout/stderr from import.

    Returns (error_messages, captured_stdout, module, module_name)
    where error_messages is empty on success or a list of error lines.
    The caller must call unload_module(module_name) after use.
    """
    mod_name = f"hosted.{uuid.uuid4().hex}"
    spec = importlib.util.spec_from_file_location(mod_name, app_file)
    if spec is None or spec.loader is None:
        return [f"error: cannot load {app_file}"], "", None, ""

    os.environ["YAK_ENDPOINT"] = "inprocess://"

    ctx = SdkContext.from_dict(_build_context_dict(space, target_path))
    sdk_context._set(ctx)

    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    buf = StringIO()
    err_buf = StringIO()
    with redirect_stdout(buf), redirect_stderr(err_buf):
        spec.loader.exec_module(mod)

    return [], buf.getvalue(), mod, mod_name


def unload_module(mod_name: str) -> None:
    """Remove a dynamically loaded module from sys.modules."""
    if mod_name in sys.modules:
        del sys.modules[mod_name]


def emit_output(output: str) -> list:
    """Return Outcome list from captured stdout."""
    if not output:
        return []
    outcomes = []
    for i, line in enumerate(output.splitlines()):
        line = line.strip()
        mode = "replace" if i == 0 else "append"
        if line.startswith("{"):
            try:
                data = _json.loads(line)
                if isinstance(data, dict) and data.get("kind") == "document":
                    outcomes.append(Outcome(effects=[EmitView(data, mode=mode)]))
                    continue
            except Exception:
                pass
        outcomes.append(Outcome(effects=[EmitView(to_text(line), mode=mode)]))
    return outcomes
