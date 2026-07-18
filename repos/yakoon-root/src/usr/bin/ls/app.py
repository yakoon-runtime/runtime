from pathlib import Path

import yaml
from y5n.sdk import context, ports

_KIND_ORDER = {"dir": 0, "cmd": 1, "file": 2}


async def main():
    req = context.request()
    target_name = req.arg(0)
    use_list = req.has_option("long") or req.has_option("l")
    show_all = req.has_option("all")

    ctx = context.current()
    root = Path(ctx.workspace) if ctx.workspace else Path.home() / "_yak"
    fs_path = _resolve_fs_path(ctx, root, target_name)
    if not fs_path.exists():
        doc = ports.get("document")
        result = await doc.render(
            name="default",
            state={"view": "default", "key": target_name or fs_path.name},
        )
        print(result)
        return

    expose = False
    yak_meta_path = fs_path / "_yak" / "yak.yml"
    if yak_meta_path.is_file():
        with open(yak_meta_path) as f:
            meta = yaml.safe_load(f) or {}
        expose = meta.get("expose", False)

    tree_path = _tree_path(ctx, target_name)
    src = ports.get("source")
    result = await src.read(query=f"system:nodes --children {tree_path}")
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
        doc = ports.get("document")
        result = await doc.render(
            name="long",
            state={
                "view": "long",
                "entries": merged,
                "path": tree_path,
            },
        )
        print(result)
        return

    items = [f"{e['key']}/" if e.get("navigable") else e["key"] for e in merged]
    doc = ports.get("document")
    result = await doc.render(
        name="default",
        state={"view": "default", "items": items},
    )
    print(result)


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


def _resolve_fs_path(ctx, root: Path, target: str | None) -> Path:
    if target and target.startswith("/"):
        return root / target.lstrip("/")
    raw = ctx.cwd
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


def _tree_path(ctx, target: str | None) -> str:
    raw = ctx.cwd or "/"
    if target:
        if target.startswith("/"):
            return target
        return f"{raw}/{target}"
    return raw
