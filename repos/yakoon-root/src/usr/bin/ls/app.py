from pathlib import Path

import yaml
from y5n.api.data import DataRequest
from y5n.api.dsl import out
from y5n.api.nodes import NodeSpace
from y5n.api.ports import PROJECT, SOURCE_READ

_KIND_ORDER = {"dir": 0, "cmd": 1, "file": 2}


async def run(space: NodeSpace):
    target_name = space.request.arg(0)
    use_list = space.request.has_option("long") or space.request.has_option("l")
    show_all = space.request.has_option("all")

    root = _root_path(space)
    fs_path = _resolve_fs_path(space, root, target_name)
    if not fs_path.exists():
        projection = await space.ports.get(PROJECT)(
            space=space,
            state={"view": "default", "key": target_name or fs_path.name},
        )
        yield out(projection)
        return

    # Check if the current package exposes all children (transparent container)
    expose = False
    yak_meta_path = fs_path / "_yak" / "yak.yml"
    if yak_meta_path.is_file():
        with open(yak_meta_path) as f:
            meta = yaml.safe_load(f) or {}
        expose = meta.get("expose", False)

    tree_path = _tree_path(space, target_name)
    on_source = space.ports.get(SOURCE_READ)
    result = await on_source(DataRequest(f"system:nodes --children {tree_path}"))
    node_map = {r["key"]: r for r in result.rows} if result.status == "ok" else {}

    fs_entries = sorted(
        fs_path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())
    )
    if not show_all:
        fs_entries = [
            p
            for p in fs_entries
            if not p.name.startswith("_yak")
            and not p.name.startswith(".")
            and not p.name.startswith("__")
        ]

    # Yak-Package-Rule: inside a strict package (not exposed) only show
    # Yak objects known to the tree (via node_map).  Files and plain
    # directories without a tree node are private implementation.
    # Fallback: only subdirs with their own _yak/.
    if (fs_path / "_yak").is_dir() and not show_all and not expose:
        if node_map:
            fs_entries = [p for p in fs_entries if p.name in node_map]
        else:
            fs_entries = [p for p in fs_entries if (p / "_yak").is_dir()]

    merged = []
    for p in fs_entries:
        is_dir = p.is_dir()
        node = node_map.get(p.name)
        kind = node.get("kind") if node else ("dir" if is_dir else "file")
        size = ""
        if use_list and kind != "dir":
            raw_size = _content_size(p) if is_dir else p.stat().st_size
            size = _format_size(raw_size)
        if node:
            row = dict(node)
            row["size"] = size
            merged.append(row)
        else:
            merged.append(
                {
                    "key": p.name,
                    "name": p.name,
                    "kind": "dir" if is_dir else "file",
                    "navigable": is_dir,
                    "listed": True,
                    "executor": None,
                    "version": None,
                    "size": size,
                }
            )

    merged.sort(key=_sort_key)

    if use_list:
        projection = await space.ports.get(PROJECT)(
            space=space,
            state={
                "view": "long",
                "entries": merged,
                "path": tree_path,
            },
        )
        yield out(projection)
        return

    items = [f"{e['key']}/" if e.get("navigable") else e["key"] for e in merged]
    projection = await space.ports.get(PROJECT)(
        space=space,
        state={"view": "default", "items": items},
    )
    yield out(projection)


def _sort_key(entry: dict) -> tuple:
    return (
        _KIND_ORDER.get(entry.get("kind", "file"), 99),
        entry.get("key", "").lower(),
    )


def _content_size(path: Path) -> int:
    total = 0
    for p in path.rglob("*"):
        if p.is_file():
            total += p.stat().st_size
    return total


def _format_size(st_size: float) -> str:
    for unit in ("B", "KiB", "MiB", "GiB"):
        if st_size < 1024:
            return f"{st_size:.0f} {unit}" if unit == "B" else f"{st_size:.1f} {unit}"
        st_size /= 1024
    return f"{st_size:.1f} TiB"


def _root_path(space) -> Path:
    raw = space.session.get_data("fs:root")
    return Path(raw) if raw else Path.home() / "_yak"


def _resolve_fs_path(space, root: Path, target: str | None) -> Path:
    if target and target.startswith("/"):
        return root / target.lstrip("/")
    raw = space.session.cwd
    if raw and raw != "/":
        tree_test = root / raw.lstrip("/")
        if tree_test.exists():
            current = tree_test
        else:
            current = Path(raw).resolve()
    else:
        current = root
    if target:
        current = current / target
    return current


def _tree_path(space, target: str | None) -> str:
    raw = space.session.cwd or "/"
    if target:
        if target.startswith("/"):
            return target
        return f"{raw}/{target}"
    return raw
