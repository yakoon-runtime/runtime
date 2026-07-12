from pathlib import Path

from y5n.api.dsl import out_text
from y5n.api.nodes import NodeSpace


def _get_root(space: NodeSpace) -> Path:
    raw = space.session.get_data("fs:root")
    return Path(raw) if raw else Path.home() / ".yak"


def _get_cwd(space: NodeSpace) -> Path:
    raw = space.session.get_data("fs:cwd")
    return Path(raw) if raw else _get_root(space)


def _set_cwd(space: NodeSpace, path: Path) -> None:
    # Store raw path (may contain symlinks) so that cd .. from
    # /crm goes back to root, not to the resolved parent.
    space.session.set_data("fs:cwd", str(path))


async def run(space: NodeSpace):

    target = space.request.arg(0)
    if not target:
        yield out_text("")
        return

    current_path = _get_cwd(space)

    root = _get_root(space)

    if target == "/":
        _set_cwd(space, root)
        yield out_text("")
        return

    if target == "..":
        _set_cwd(space, current_path.parent)
        yield out_text("")
        return

    resolved = (root / target.lstrip("/")) if target.startswith("/") else (current_path / Path(target))
    resolved = resolved.resolve()

    if not resolved.exists():
        yield out_text(f"Not found: {resolved}")
        return

    if not resolved.is_dir():
        yield out_text(f"Not a directory: {resolved}")
        return

    _set_cwd(space, resolved)
    yield out_text("")
