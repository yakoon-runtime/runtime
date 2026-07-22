import importlib
import inspect
import os
from pathlib import Path

from y5n.runtime.api import Outcome, to_text
from y5n.runtime.api.host import HANDLERS, MarkerKind, drive
from y5n.runtime.api import EmitView, NodeSpace
from y5n.sdk import context as sdk_context
from y5n.sdk.libs.models import Context as SdkContext

from ._shared import (
    _build_context_dict,
    build_app_file,
    load_and_capture,
    read_entry,
    resolve_tree_path,
    unload_module,
)


async def run(space: NodeSpace):
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

    entry = read_entry(root, target_path)
    if not entry:
        yield Outcome(effects=[EmitView(to_text(f"error: no entry for '{target_path}'"))])
        return

    from ._shared import parse_entry

    try:
        scheme, value = parse_entry(entry)
    except ValueError as e:
        yield Outcome(effects=[EmitView(to_text(str(e)))])
        return

    if scheme == "pack":
        os.environ.setdefault("YAK_ENDPOINT", "inprocess://")
        mod_name, _, func_name = value.rpartition(":")
        if not mod_name or not func_name:
            yield Outcome(
                effects=[EmitView(to_text(f"error: invalid pack entry '{value}'"))]
            )
            return
        try:
            mod = importlib.import_module(mod_name)
        except ImportError as e:
            yield Outcome(
                effects=[EmitView(to_text(f"error: cannot import {mod_name}: {e}"))]
            )
            return
        main_fn = getattr(mod, func_name, None)
        if main_fn is None:
            yield Outcome(
                effects=[EmitView(to_text(f"error: {mod_name} has no '{func_name}'"))]
            )
            return
        ctx = SdkContext.from_dict(_build_context_dict(space, target_path))
        sdk_context._set(ctx)
        mod_name_for_cleanup = ""
    elif scheme == "file":
        app_file = root / value
        if not app_file.is_file():
            yield Outcome(
                effects=[EmitView(to_text(f"error: file not found: '{app_file}'"))]
            )
            return

        errors, _, mod, mod_name_for_cleanup = load_and_capture(
            space, target_path, app_file
        )
        if errors:
            for err in errors:
                yield Outcome(effects=[EmitView(to_text(err))])
            return

        main_fn = getattr(mod, "main", None)
        if main_fn is None:
            yield Outcome(effects=[EmitView(to_text("error: command has no main()"))])
            return
    else:
        yield Outcome(effects=[EmitView(to_text(f"error: unknown scheme '{scheme}'"))])
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

    session = space.session
    flow_id = space.flow_id

    def _flows_list(exclude_id: str) -> list[dict]:
        result = []
        fg = session.foreground_flow
        exclude = exclude_id or flow_id or None
        for idx, flow in enumerate(session.flows(exclude=exclude), start=1):
            result.append(
                {
                    "index": idx,
                    "id": flow.id,
                    "label": flow.node.name or flow.node.key,
                    "state": flow.control.label() if flow.control else "run",
                    "foreground": bool(fg) and fg.id == flow.id,
                }
            )
        return result

    def _flow_stop(flow_id: str) -> None:
        flow = session.get_flow(flow_id)
        if flow:
            session.del_flow(flow)

    def _flow_fg(flow_id: str) -> None:
        session.set_foreground_flow(flow_id)

    def _flow_bg(_: None) -> dict | None:
        fg = session.foreground_flow
        if not fg:
            return None
        session.set_foreground_flow(None)
        return {"id": fg.id, "label": fg.node.name or fg.node.key}

    try:
        async for outcome in drive(
            coro,
            HANDLERS,
            side_effects={
                MarkerKind.CWD: lambda path: session.set_cwd(path),
                MarkerKind.FLOW_STOP: _flow_stop,
                MarkerKind.FLOW_FG: _flow_fg,
            },
            responses={
                MarkerKind.FLOWS_LIST: _flows_list,
                MarkerKind.FLOW_BG: _flow_bg,
            },
        ):
            yield outcome
    except Exception as e:
        yield Outcome(effects=[EmitView(to_text(f"error: {e}"))])

    if mod_name_for_cleanup and mod_name_for_cleanup.startswith("yak.bundle"):
        unload_module(mod_name_for_cleanup)
    yield Outcome()
