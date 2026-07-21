import os
from pathlib import Path

from y5n.sdk import context, fs, io


async def main():
    req = context.request()
    target = req.arg(0)

    if not target:
        await io.write("")
        return

    ctx = context.current()
    current_path = _get_cwd(ctx)
    root = _get_root(ctx)

    if target == "/":
        await fs.chdir("/")
        await io.write("")
        return

    if target == "..":
        await fs.chdir(_to_display(current_path.parent, root))
        await io.write("")
        return

    if target == "~":
        home = Path.home()
        display = ("/" + home.name) if home.name else str(home)
        await fs.chdir(display)
        await io.write("")
        return

    raw = (
        (root / target.lstrip("/"))
        if target.startswith("/")
        else (current_path / Path(target))
    )
    resolved = raw.resolve()

    if not resolved.exists():
        await io.write(f"Not found: {resolved}")
        return

    if not resolved.is_dir():
        await io.write(f"Not a directory: {resolved}")
        return

    display = _to_display(raw, root)
    await fs.chdir(display)
    await io.write("")


def _get_root(ctx) -> Path:
    raw = ctx.workspace
    return Path(raw).resolve() if raw else Path.home() / "_yak"


def _get_cwd(ctx) -> Path:
    raw = ctx.cwd
    if not raw or raw == "/":
        return _get_root(ctx)
    root = _get_root(ctx)
    tree_test = root / raw.lstrip("/")
    if tree_test.exists():
        return tree_test
    return Path(raw).resolve()


def _to_display(path: Path, root: Path) -> str:
    resolved = path.resolve()
    root_abs = root.resolve()
    normal = Path(os.path.normpath(str(path)))
    try:
        rel = normal.relative_to(root_abs)
        return "/" + str(rel) if str(rel) != "." else "/"
    except ValueError:
        try:
            rel = resolved.relative_to(root_abs)
            return "/" + str(rel) if str(rel) != "." else "/"
        except ValueError:
            return str(resolved)
