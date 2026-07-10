from pathlib import Path

from y5n.api.dsl import out
from y5n.api.nodes import NodeSpace
from y5n.api.projections import to_text

from ...ports import OnProject


def _get_cwd(space: NodeSpace) -> Path:
    raw = space.session.get_data("fs:cwd")
    if not raw:
        raw = space.session.get_data("fs:root", str(Path.home() / ".yakoon"))
    return Path(raw).resolve()


# ----------------------------------
# RUN
# ----------------------------------


async def run(space: NodeSpace):

    show_all = space.request.has_option("all")
    target_name = space.request.arg(0)

    current_path = _get_cwd(space)

    # ----------------------------------
    # RESOLVE PATH
    # ----------------------------------

    target = current_path / target_name if target_name else current_path
    target = target.resolve()

    if not target.exists():
        yield out(to_text(f"Not found: {target}"))
        return

    if not target.is_dir():
        yield out(to_text(f"{target.name}"))
        return

    # ----------------------------------
    # LIST DIRECTORY
    # ----------------------------------

    entries = sorted(target.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))

    dirs = []
    files = []

    for p in entries:
        is_dir = p.is_dir()
        if is_dir:
            dirs.append({"name": p.name, "is_dir": True, "size": 0})
        else:
            try:
                size = p.stat().st_size
            except OSError:
                size = 0
            files.append({"name": p.name, "is_dir": False, "size": size})

    # ----------------------------------
    # PROJECT
    # ----------------------------------

    projection = await space.ports.get(OnProject)(
        name="system/ls",
        lang=space.session.lang,
        state={
            "dirs": dirs,
            "files": files,
            "path": str(target),
        },
    )

    yield out(projection)
