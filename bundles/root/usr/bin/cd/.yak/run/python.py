from pathlib import Path

from y5n.api.dsl import out_text
from y5n.api.nodes import NodeSpace


async def run(space: NodeSpace):

    target = space.request.arg(0)
    if not target:
        yield out_text("")
        return

    current_path = _get_cwd(space)
    root = _get_root(space)

    if target == "/":
        _set_path(space, root, root)
        yield out_text("")
        return

    if target == "..":
        _set_path(space, current_path.parent, root)
        yield out_text("")
        return

    raw = (
        (root / target.lstrip("/"))
        if target.startswith("/")
        else (current_path / Path(target))
    )
    resolved = raw.resolve()

    if not resolved.exists():
        yield out_text(f"Not found: {resolved}")
        return

    if not resolved.is_dir():
        yield out_text(f"Not a directory: {resolved}")
        return

    _set_path(space, raw, root)
    yield out_text("")


# ----------------------------
# INTERNALS
# ----------------------------


def _get_root(space: NodeSpace) -> Path:
    raw = space.session.get_data("fs:root")
    return Path(raw) if raw else Path.home() / ".yak"


def _get_cwd(space: NodeSpace) -> Path:
    raw = space.session.get_current_path()
    if not raw:
        return _get_root(space)
    # "/" means yakoon root, not Linux root
    if raw == "/":
        return _get_root(space).resolve()
    return Path(raw).resolve()


def _set_path(space: NodeSpace, path: Path, root: Path) -> None:
    resolved = path.resolve()
    try:
        rel = resolved.relative_to(root.resolve())
        display = "/" + str(rel) if str(rel) != "." else "/"
    except ValueError:
        display = str(resolved)
    space.session.set_current_path(display)
