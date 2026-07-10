from pathlib import Path

from y5n.api.dsl import out_text
from y5n.api.nodes import NodeSpace

# ----------------------------------
# HELPERS
# ----------------------------------

ROOT = "/"


def _get_cwd(space: NodeSpace) -> Path:
    raw = space.session.get_data("fs:cwd", str(Path.home() / ".yakoon" / "test"))
    return Path(raw).resolve()


def _set_cwd(space: NodeSpace, path: Path) -> None:
    space.session.set_data("fs:cwd", str(path.resolve()))


# ----------------------------------
# RUN
# ----------------------------------


async def run(space: NodeSpace):

    target = space.request.arg(0)
    if not target:
        yield out_text("")
        return

    current_path = _get_cwd(space)

    # ----------------------------------
    # ROOT
    # ----------------------------------

    if target == ROOT:
        _set_cwd(space, Path(ROOT))
        yield out_text("")
        return

    # ----------------------------------
    # PARENT
    # ----------------------------------

    if target == "..":
        parent = current_path.parent
        _set_cwd(space, parent)
        yield out_text("")
        return

    # ----------------------------------
    # PATH
    # ----------------------------------

    raw = Path(target)
    resolved = raw if target.startswith(ROOT) else (current_path / raw)
    resolved = resolved.resolve()

    # ----------------------------------
    # VALIDATE TARGET
    # ----------------------------------

    if not resolved.exists():
        yield out_text(f"Not found: {resolved}")
        return

    if not resolved.is_dir():
        yield out_text(f"Not a directory: {resolved}")
        return

    # ----------------------------------
    # ACTIVATE
    # ----------------------------------

    _set_cwd(space, resolved)
    yield out_text("")
